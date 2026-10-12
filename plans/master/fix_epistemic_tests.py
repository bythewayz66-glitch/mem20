"""Repair the remember()/supersede() epistemic_status contract break in memory_engine tests.

AST-based: adds `epistemic_status="observed"` only to calls that (a) target
remember/supersede, (b) omit epistemic_status, (c) are not the deliberate
`_allow_simulated=True` negative test, which must keep raising PermissionError.
"""
import ast
import sys

FILES = sys.argv[1:] or [
    "memory_engine/tests/test_recall_at_bitemporal.py",
    "memory_engine/tests/test_event_time_provenance.py",
    "memory_engine/tests/test_grounded_firewall.py",
    "memory_engine/tests/test_pii_non_destructive.py",
]

STATUS = '"observed"'


def repair(path):
    src = open(path).read()
    tree = ast.parse(src)
    # Collect (insert_offset, line, col, funcname) for calls needing the kwarg.
    inserts = []  # (offset, text, name, lineno)
    lines = src.splitlines(keepends=True)
    offsets = []
    off = 0
    for ln in lines:
        offsets.append(off)
        off += len(ln)

    def pos(lineno, col):
        return offsets[lineno - 1] + col

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name not in ("remember", "supersede"):
            continue
        kws = {k.arg for k in node.keywords}
        if "epistemic_status" in kws:
            continue
        if any(
            k.arg == "_allow_simulated"
            for k in node.keywords
        ):
            continue  # deliberate negative test for the simulated firewall
        # Insert immediately before the CLOSING paren so positional args stay
        # positional. Inserting first would break supersede(old_id, content).
        end = pos(node.end_lineno, node.end_col_offset)  # just past ')'
        close = end - 1
        # Look back past whitespace for a dangling comma or an empty arg list.
        j = close - 1
        while j >= 0 and src[j] in " \t\r\n":
            j -= 1
        if src[j] == ",":
            sep = " "                      # already trailing-comma'd
        elif src[j] == "(":
            sep = ""                       # no arguments at all
        else:
            sep = ", "
        inserts.append((close, sep + f"epistemic_status={STATUS}", name, node.lineno))

    if not inserts:
        return 0
    # Apply right-to-left so offsets stay valid.
    inserts.sort(reverse=True)
    out = src
    for idx, text, name, lineno in inserts:
        out = out[:idx] + text + out[idx:]
    open(path, "w").write(out)
    return len(inserts)


total = 0
for f in FILES:
    n = repair(f)
    print(f"{f}: patched {n} call(s)")
    total += n
print("TOTAL patched:", total)