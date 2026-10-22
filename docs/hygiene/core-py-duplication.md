# core.py duplication (issue #17)

Shared package: `mem20corez`.

Migrate identical cores:
```python
from mem20corez import *  # noqa: F401,F403
```

Do not delete packages.
