# mem20audiovoiceandmusicpipelinez — Audio, Voice & Music Pipeline

Mix tracks, normalize audio, sync to beats, export formats, and apply mastering chains, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20audiovoiceandmusicpipelinez.domain import (
    mix_tracks, normalize, sync_to_beat, export_format, mastering_chain, estate_context,
)

print(mix_tracks([{"id": "vox", "samples": [0.1, 0.2]}], volumes=[0.8]))
print(normalize([0.5, 1.0, -0.8], target_db=-3.0))
print(sync_to_beat(audio_len_s=10.0, bpm=120))
print(export_format([0] * 44100, fmt="wav", sample_rate=44100))
print(mastering_chain(["limit"], [1.5, -1.2, 0.2]))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20audiovoiceandmusicpipelinez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20audiovoiceandmusicpipelinez/mem20audiovoiceandmusicpipelinez/tests -q
```
