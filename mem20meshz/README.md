# mem20 Mesh Gold Runtime

Six domain mesh engines are **vendored** under `mem20meshz.meshes`:

- crisis (ex `mem20crisisresponsemeshz`)
- crossdevice (ex `mem20crossdevicememorymeshz`)
- federated (ex `mem20federatedmodellearningmeshz`)
- nearby (ex `mem20nearbydevicemeshz`)
- offline (ex `mem20offlineresiliencemeshz`)
- selfhealing (ex `mem20selfhealingconnectormeshz`)

The old top-level packages are removed after consolidation.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20meshz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20meshz list
```
