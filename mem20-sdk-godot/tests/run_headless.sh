#!/usr/bin/env bash
# Headless round-trip test for the mem20 Godot addon.
#
# Needs the `godot4` binary (override with GODOT=/path/to/godot) and a mem20
# checkout with its Python dependencies installed. Set MEM20_ROOT to test a
# different checkout; it defaults to the repository this script lives in.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sdk="$(cd "$here/.." && pwd)"
repo="$(cd "$sdk/.." && pwd)"
godot="${GODOT:-godot4}"

if ! command -v "$godot" >/dev/null 2>&1; then
	echo "godot binary not found: $godot (set GODOT=/path/to/godot)" >&2
	exit 2
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/mem20-godot-test.XXXXXX")"
fixture_pid=""
cleanup() {
	if [ -n "$fixture_pid" ]; then
		kill "$fixture_pid" 2>/dev/null || true
		wait "$fixture_pid" 2>/dev/null || true
	fi
	rm -rf "$tmp"
}
trap cleanup EXIT

mkdir -p "$tmp/addons" "$tmp/store"
cp -R "$sdk/addons/mem20" "$tmp/addons/mem20"
cp "$here/roundtrip.gd" "$tmp/roundtrip.gd"
cp "$here/main.tscn" "$tmp/main.tscn"

cat > "$tmp/project.godot" <<'PROJECT'
[application]

config/name="mem20 godot roundtrip"
config/features=PackedStringArray("4.3")
run/main_scene="res://main.tscn"

[rendering]

renderer/rendering_method="gl_compatibility"
PROJECT

port="$("${PYTHON:-python3}" - <<'PY'
import socket
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)"

"${PYTHON:-python3}" "$here/health_fixture.py" "$port" &
fixture_pid=$!

for _ in $(seq 1 50); do
	if "${PYTHON:-python3}" - "$port" <<'PY'
import socket, sys
sock = socket.socket()
sock.settimeout(0.2)
try:
    sock.connect(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
	then
		break
	fi
	sleep 0.1
done

export MEM20_ROOT="${MEM20_ROOT:-$repo}"
export MEM20_TEST_HEALTH_PORT="$port"
export MEM20_TEST_STORE="$tmp/store"
export MEM20_STORE_PATH="$tmp/store"

"$godot" --headless --path "$tmp" --import >/dev/null
"$godot" --headless --path "$tmp"
