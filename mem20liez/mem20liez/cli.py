"""fs-lie CLI — live capture, baseline, offline analyze."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fs-lie", description="mem20liez live behavioural signals")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_live = sub.add_parser("live", help="Live mic or WAV → cues → seal")
    p_live.add_argument("--mode", default="generic",
                        choices=["interrogation", "therapy", "clinical", "government", "generic"])
    p_live.add_argument("--duration", type=float, default=15.0, help="seconds (mic mode)")
    p_live.add_argument("--wav", default=None, help="WAV file instead of mic")
    p_live.add_argument("--no-earpiece", action="store_true")
    p_live.add_argument("--out", default=None, help="write sealed package JSON")

    p_status = sub.add_parser("status", help="Show detector / backend status")

    args = parser.parse_args(argv)

    if args.cmd == "status":
        from .live import _try_import_sounddevice, _try_import_pyaudio, EarpieceTTS
        from .detectors.voice_stress import HAS_NUMPY as VS_NP
        from .detectors.micro_expression import HAS_NUMPY as ME_NP, HAS_PIL
        tts = EarpieceTTS()
        print(json.dumps({
            "voice_stress_numpy": VS_NP,
            "micro_expression_numpy": ME_NP,
            "micro_expression_pil": HAS_PIL,
            "mic_sounddevice": _try_import_sounddevice() is not None,
            "mic_pyaudio": _try_import_pyaudio() is not None,
            "tts_backend": tts.backend,
        }, indent=2))
        return 0

    if args.cmd == "live":
        from .live import run_live_session
        try:
            result = run_live_session(
                mode=args.mode,
                duration_s=args.duration,
                wav_path=args.wav,
                enable_earpiece=not args.no_earpiece,
            )
        except RuntimeError as e:
            print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
            return 1
        summary = {"ok": True, "stats": result["stats"], "package_summary": result["package_summary"]}
        print(json.dumps(summary, indent=2))
        if args.out:
            with open(args.out, "w") as f:
                json.dump(result["package"], f, indent=2, default=str)
            print(f"wrote {args.out}", file=sys.stderr)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
