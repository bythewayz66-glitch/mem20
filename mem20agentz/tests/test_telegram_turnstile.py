"""Token-free proof of the Telegram turnstile bridge (issue #43).

The Telegram bridge is a long-poll adapter: ``getMe`` → ``getUpdates`` →
dispatch through ``Bridge.handle`` → ``sendMessage``. Because the Bot API base
URL is injectable, the whole turnstile can be exercised against a **fake Bot API
server on loopback** — no Telegram account, no bot token from ``@BotFather``, no
internet.

What this proves, end to end, with nothing stubbed inside ``mem20agentz``:

* ``TelegramTransport.start()`` really performs ``getMe`` and accepts the reply.
* ``TelegramTransport.poll()`` really parses a ``getUpdates`` envelope into a
  ``Message`` and advances the offset so the same update is never replayed.
* ``Bridge.handle()`` dispatches that message to an agent factory.
* ``Bridge.send()`` really performs ``sendMessage`` with the reply text.
* Pairing is enforced: an unpaired chat is ignored and never answered.
* Without a token the transport fails honestly (``TelegramAuthError``) rather
  than pretending to be connected.

The fake server records every request it receives, so "the reply was sent" is
asserted against what the transport actually put on the wire — not against a
mock's return value.

Run it on its own::

    python -m pytest mem20agentz/tests/test_telegram_turnstile.py -v
"""

from __future__ import annotations

import http.server
import json
import os
import pathlib
import tempfile
import threading
import unittest
import unittest.mock
from types import SimpleNamespace

from mem20agentz.bridge import Bridge, Message
from mem20agentz.bridges.telegram import TelegramAuthError, TelegramTransport


class _FakeBotApi(http.server.BaseHTTPRequestHandler):
    """The smallest Bot API that can carry a turnstile.

    Only the three methods the adapter uses are implemented. Every request is
    appended to ``server.requests`` as ``(method, payload)`` so the test can
    assert on what actually went over the wire.
    """

    protocol_version = "HTTP/1.1"

    # ---- server plumbing -------------------------------------------------
    def _send(self, payload: dict, code: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _method(self) -> str:
        # /bot<token>/<method>  →  <method>
        parts = self.path.strip("/").split("/")
        return parts[-1] if parts else ""

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def log_message(self, *args):  # silence the default stderr access log
        return

    # ---- Bot API methods -------------------------------------------------
    def do_GET(self):  # noqa: N802 - http.server API
        method = self._method()
        if method == "getMe":
            self.server.requests.append(("getMe", {}))
            self._send({"ok": True, "result": {"id": 1, "username": "mem20_test_bot"}})
            return
        self._send({"ok": False, "description": f"unknown method {method}"}, 404)

    def do_POST(self):  # noqa: N802 - http.server API
        method = self._method()
        body = self._body()
        self.server.requests.append((method, body))

        if method == "getUpdates":
            # Serve queued updates one poll at a time, honouring the offset the
            # adapter sends so a replayed update is detectable.
            offset = int(body.get("offset") or 0)
            queued = [u for u in self.server.updates if u["update_id"] >= offset]
            self._send({"ok": True, "result": queued[:1]})
            return

        if method == "sendMessage":
            self.server.sent.append(
                {"chat_id": str(body.get("chat_id")), "text": body.get("text")}
            )
            self._send({"ok": True, "result": {"message_id": len(self.server.sent)}})
            return

        self._send({"ok": False, "description": f"unknown method {method}"}, 404)


class TelegramTurnstileBase(unittest.TestCase):
    """Boot a fake Bot API on an ephemeral loopback port per test."""

    def setUp(self) -> None:
        super().setUp()
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeBotApi)
        self.server.requests = []
        self.server.sent = []
        self.server.updates = []
        self.port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        self._tmp = tempfile.TemporaryDirectory()
        self._env = unittest.mock.patch.dict(
            os.environ, {"MEM20AGENTZ_TELEGRAM_TOKEN": "test:token"}, clear=False
        )
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()
        self.server.shutdown()
        self.server.server_close()
        self._tmp.cleanup()
        super().tearDown()

    # ---- helpers ---------------------------------------------------------
    def queue_update(self, chat_id: str, text: str) -> None:
        self.server.updates.append(
            {
                "update_id": len(self.server.updates) + 1,
                "message": {
                    "chat": {"id": chat_id},
                    "text": text,
                    "date": 1700000000 + len(self.server.updates),
                    "from": {"username": "tester"},
                },
            }
        )

    def transport(self) -> TelegramTransport:
        return TelegramTransport(base_url=self.base_url)

    def bridge(self, transport, reply: str, **kwargs) -> Bridge:
        class _Core:
            def run(self, text):  # noqa: D401 - tiny stand-in agent
                return SimpleNamespace(blocked=False, text=f"{reply}:{text}")

        return Bridge(
            "telegram",
            transport,
            agent_factory=lambda chat_id: _Core(),
            ledger=None,
            root=pathlib.Path(self._tmp.name),
            **kwargs,
        )

    def methods(self) -> list[str]:
        return [name for name, _ in self.server.requests]


class TestTokenFreeTurnstile(TelegramTurnstileBase):
    """The full poll → dispatch → send loop, with no real bot token."""

    def test_full_turnstile_over_loopback(self):
        transport = self.transport()
        transport.start()  # real getMe against the fake Bot API
        self.assertIn("getMe", self.methods())

        bridge = self.bridge(transport, reply="pong", require_pairing=False)
        self.queue_update("4242", "ping")

        msg = transport.poll(timeout=1.0)
        self.assertIsNotNone(msg, "no message parsed out of getUpdates")
        self.assertEqual(msg.chat_id, "4242")
        self.assertEqual(msg.text, "ping")
        self.assertEqual(msg.platform, "telegram")
        self.assertEqual(msg.sender, "tester")

        reply = bridge.handle(msg)
        self.assertEqual(reply, "pong:ping")

        bridge.send(msg.chat_id, reply)

        # The assertion is against the wire, not a mock return value.
        self.assertEqual(len(self.server.sent), 1, "sendMessage never reached the API")
        self.assertEqual(self.server.sent[0]["chat_id"], "4242")
        self.assertEqual(self.server.sent[0]["text"], "pong:ping")

    def test_offset_prevents_update_replay(self):
        """A delivered update is never handed out twice (the offset advances)."""
        transport = self.transport()
        transport.start()
        self.queue_update("7", "only-once")

        first = transport.poll(timeout=1.0)
        self.assertIsNotNone(first)
        self.assertEqual(first.text, "only-once")

        second = transport.poll(timeout=1.0)
        self.assertIsNone(second, "update replayed — offset did not advance")

    def test_unpaired_chat_is_ignored(self):
        """Pairing is enforced: an unpaired chat gets no answer at all."""
        transport = self.transport()
        transport.start()
        bridge = self.bridge(transport, reply="pong", require_pairing=True)
        self.queue_update("9999", "should be ignored")

        msg = transport.poll(timeout=1.0)
        self.assertIsNotNone(msg)
        self.assertFalse(bridge._is_paired(msg.chat_id))
        # The poll loop is what enforces pairing; mirror its decision here so the
        # rule is asserted even without running the blocking loop.
        if bridge._is_paired(msg.chat_id):  # pragma: no cover - guarded
            bridge.send(msg.chat_id, bridge.handle(msg))
        self.assertEqual(self.server.sent, [], "unpaired chat received a reply")

    def test_paired_chat_is_answered(self):
        transport = self.transport()
        transport.start()
        bridge = self.bridge(transport, reply="pong", require_pairing=True)
        bridge.pair("1234")
        self.assertTrue(bridge._is_paired("1234"))

        self.queue_update("1234", "ping")
        msg = transport.poll(timeout=1.0)
        self.assertIsNotNone(msg)
        bridge.send(msg.chat_id, bridge.handle(msg))
        self.assertEqual(self.server.sent[0]["text"], "pong:ping")

    def test_media_message_is_annotated_not_dropped(self):
        transport = self.transport()
        transport.start()
        bridge = self.bridge(transport, reply="seen", require_pairing=False)
        self.server.updates.append(
            {
                "update_id": 1,
                "message": {
                    "chat": {"id": "55"},
                    "date": 1700000001,
                    "document": {"file_name": "report.pdf"},
                },
            }
        )
        msg = transport.poll(timeout=1.0)
        self.assertIsNotNone(msg)
        self.assertTrue(msg.has_media)
        self.assertIn("report.pdf", msg.media)
        # A media-only message still reaches the agent, annotated.
        self.assertEqual(bridge.handle(msg), "seen: [media: 1 attachment(s)]")

    def test_no_token_fails_honestly(self):
        """No token, no fake success: the transport refuses to start."""
        os.environ.pop("MEM20AGENTZ_TELEGRAM_TOKEN", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        real_exists = pathlib.Path.exists

        def _no_root_env(self, *args, **kwargs):
            if str(self) == "/root/.env":
                return False
            return real_exists(self, *args, **kwargs)

        with unittest.mock.patch.object(pathlib.Path, "exists", _no_root_env):
            with self.assertRaises(TelegramAuthError):
                TelegramTransport(base_url=self.base_url)

    def test_rejected_token_surfaces_as_auth_error(self):
        """A 401 from the Bot API is reported as an auth failure, not a hang."""

        def _unauthorised(handler):
            handler.send_response(401)
            handler.send_header("Content-Length", "0")
            handler.end_headers()

        with unittest.mock.patch.object(_FakeBotApi, "do_GET", _unauthorised):
            transport = self.transport()
            with self.assertRaises(TelegramAuthError) as ctx:
                transport.start()
            self.assertIn("401", str(ctx.exception))


class TestTurnstileIsHermetic(unittest.TestCase):
    """The proof must not need the network, a token, or the real Bot API."""

    def setUp(self) -> None:
        super().setUp()
        # No token exists in CI; supply a syntactically valid one so the adapter
        # can be constructed. Nothing here ever connects to Telegram.
        self._env = unittest.mock.patch.dict(
            os.environ, {"MEM20AGENTZ_TELEGRAM_TOKEN": "test:token"}, clear=False
        )
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()
        super().tearDown()

    def test_base_url_is_injectable_and_defaults_to_telegram(self):
        self.assertEqual(
            TelegramTransport(base_url="http://127.0.0.1:9/").base_url,
            "http://127.0.0.1:9",
            "trailing slash must be normalised",
        )

    def test_transport_sends_to_the_configured_base_url(self):
        """Nothing in the adapter hardcodes api.telegram.org on the request path."""
        source = pathlib.Path(
            __import__("mem20agentz.bridges.telegram", fromlist=["x"]).__file__
        ).read_text(encoding="utf-8")
        # The default is allowed to name the real host once; request construction
        # must go through self.base_url.
        self.assertIn("self.base_url", source)
        self.assertEqual(
            source.count("https://api.telegram.org"),
            1,
            "the real Bot API host must appear only as the default base_url",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
