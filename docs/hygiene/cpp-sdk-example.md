# C++ SDK example build (issue #25)

## Files

- `docs/sdk/cpp/examples/store_recall_audit.cpp` — end-to-end store/recall/audit example
- `mem20owebz/.../_render_amendment_stamp.cpp` — Unity asset pipeline helper (not an SDK example)

## Build the SDK example

From the repo root (requires the C++ SDK headers under `sdk/cpp` or `docs/sdk/cpp`):

```bash
make cpp-example
# or:
#   c++ -std=c++17 -c docs/sdk/cpp/examples/store_recall_audit.cpp -I docs/sdk/cpp/include
```

Full link against the SDK and a live `MEM20_SERVER` is documented in the example source header.

The Unity `_render_amendment_stamp.cpp` helper stays with the asset pipeline and is not part of the SDK CI gate.
