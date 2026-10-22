# mem20crewz — clean install tests (issue #47)

Runtime deps already include `aiohttp` and `pyyaml`.

```bash
pip install -e "./mem20crewz[dev]"
pytest mem20crewz/tests -q
```

Expected: green suite without manual extra installs.
