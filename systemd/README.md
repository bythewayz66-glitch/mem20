# systemd unit template — `systemd/`

The templated systemd unit used by the Debian package and by manual installs.

**1 tracked file(s).**

## Contents

- `mem20.service.template` — unit with `__MEM20_USER__`, `__MEM20_WORKDIR__`, `__MEM20_VENV_PYTHON__`, `__MEM20_STORE_PATH__` placeholders

## Notes

This is a **template**, not a unit. The placeholders are substituted at install
time by `packaging/deb/build-deb.sh`. Do not commit a rendered unit here.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
