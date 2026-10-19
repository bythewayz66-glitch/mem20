"""Live microphone → detector → earpiece TTS path.

Graceful dependency handling:
- Preferred: sounddevice (PortAudio)
- Fallback: pyaudio
- Always available: WAV file / raw PCM file input for offline replay
- TTS: optional pyttsx3 / system `say` / `espeak`; otherwise prints cues

This module never claims hardware is present when it is not.
"""

from __future__ import annotations

from typing import Optional, Callable, List, Any
import time
import struct
import wave
import sys
import threading
import queue

from .pipeline import LieDetector
from .session import LiveLieSession
from .types import EarpieceCue


def _try_import_sounddevice():
    try:
        import sounddevice as sd
        return sd
    except ImportError:
        return None


def _try_import_pyaudio():
    try:
        import pyaudio
        return pyaudio
    except ImportError:
        return None


class EarpieceTTS:
    """Minimal TTS for earpiece cues. Degrades to stdout."""

    def __init__(self, prefer: str = "auto"):
        self.backend = "stdout"
        self._engine = None
        if prefer in ("auto", "pyttsx3"):
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", 175)
                self.backend = "pyttsx3"
            except Exception:
                pass
        if self.backend == "stdout" and prefer in ("auto", "espeak"):
            if shutil.which("espeak") or shutil.which("espeak-ng"):
                self.backend = "espeak"
        if self.backend == "stdout" and prefer in ("auto", "say"):
            if shutil.which("say"):  # macOS
                self.backend = "say"

    def speak(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        if self.backend == "pyttsx3" and self._engine is not None:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                return
            except Exception:
                pass
        if self.backend == "espeak":
            bin_ = shutil.which("espeak-ng") or shutil.which("espeak")
            subprocess.Popen([bin_, "-v", "en", text],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if self.backend == "say":
            subprocess.Popen(["say", text],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        # Always-available fallback
        print(f"[earpiece] {text}", flush=True)


class LiveCapture:
    """Capture audio from mic or file and feed a LiveLieSession."""

    def __init__(
        self,
        session: LiveLieSession,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_ms: int = 500,
        earpiece: Optional[EarpieceTTS] = None,
        on_cue: Optional[Callable[[EarpieceCue], None]] = None,
    ):
        self.session = session
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_samples = int(sample_rate * chunk_ms / 1000)
        self.earpiece = earpiece or EarpieceTTS()
        self.on_cue = on_cue
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.stats = {"chunks": 0, "cues": 0, "backend": None}

    def _emit_cues(self) -> None:
        cues = self.session.get_earpiece_cues()
        for c in cues:
            self.stats["cues"] += 1
            if self.on_cue:
                self.on_cue(c)
            self.earpiece.speak(c.text)
            self.session.acknowledge_cue(c.id)

    def feed_pcm(self, pcm: bytes) -> None:
        self.session.feed_audio(pcm)
        self.stats["chunks"] += 1
        self._emit_cues()

    def run_wav(self, path: str) -> dict:
        """Offline replay from a WAV file (always available)."""
        self.stats["backend"] = "wav"
        with wave.open(path, "rb") as wf:
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            ch = wf.getnchannels()
            # simple: read in chunk_samples frames
            while not self._stop.is_set():
                frames = wf.readframes(self.chunk_samples)
                if not frames:
                    break
                # downmix if needed is left to detector; pass raw
                self.feed_pcm(frames)
                # paced roughly realtime
                time.sleep(self.chunk_samples / float(sr))
        return dict(self.stats)

    def run_mic(self, duration_s: Optional[float] = None) -> dict:
        """Live microphone capture. Requires sounddevice or pyaudio."""
        sd = _try_import_sounddevice()
        if sd is not None:
            return self._run_sounddevice(sd, duration_s)
        pa = _try_import_pyaudio()
        if pa is not None:
            return self._run_pyaudio(pa, duration_s)
        raise RuntimeError(
            "No live mic backend available. Install sounddevice or pyaudio, "
            "or use run_wav(path) for offline replay."
        )

    def _run_sounddevice(self, sd, duration_s: Optional[float]) -> dict:
        self.stats["backend"] = "sounddevice"
        started = time.time()

        def callback(indata, frames, time_info, status):
            if self._stop.is_set():
                raise sd.CallbackStop()
            # indata is float32; convert to int16 PCM
            clipped = indata.copy()
            if clipped.ndim > 1:
                clipped = clipped.mean(axis=1)
            pcm = (clipped * 32767.0).astype("int16").tobytes()
            self.feed_pcm(pcm)
            if duration_s and (time.time() - started) >= duration_s:
                self._stop.set()
                raise sd.CallbackStop()

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.chunk_samples,
            callback=callback,
        ):
            while not self._stop.is_set():
                time.sleep(0.05)
                if duration_s and (time.time() - started) >= duration_s:
                    break
        return dict(self.stats)

    def _run_pyaudio(self, pyaudio_mod, duration_s: Optional[float]) -> dict:
        self.stats["backend"] = "pyaudio"
        pa = pyaudio_mod.PyAudio()
        stream = pa.open(
            format=pyaudio_mod.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_samples,
        )
        started = time.time()
        try:
            while not self._stop.is_set():
                data = stream.read(self.chunk_samples, exception_on_overflow=False)
                self.feed_pcm(data)
                if duration_s and (time.time() - started) >= duration_s:
                    break
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
        return dict(self.stats)

    def stop(self) -> None:
        self._stop.set()


def run_live_session(
    mode: str = "generic",
    duration_s: Optional[float] = 30.0,
    wav_path: Optional[str] = None,
    enable_earpiece: bool = True,
) -> dict:
    """Convenience: start session, capture, seal."""
    detector = LieDetector()
    session = LiveLieSession(detector=detector, mode=mode, enable_earpiece=enable_earpiece)  # type: ignore
    tts = EarpieceTTS()
    capture = LiveCapture(session, earpiece=tts)

    if wav_path:
        stats = capture.run_wav(wav_path)
    else:
        stats = capture.run_mic(duration_s=duration_s)

    package = session.seal()
    return {"stats": stats, "package_summary": {
        "session_id": package["session_id"],
        "mode": package["mode"],
        "detections": len(package["detections"]),
        "cues": len(package["cues"]),
    }, "package": package}
