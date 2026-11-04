# Rules

- No fake code
- No placeholders
- No stubs
- No "implement later"
- No fake implementations
- Write real, working code only
- Do not add TODO/FIXME/XXX or placeholder comments
- Do not create mock/fake/dummy functions or classes
- Do not return hardcoded fake data to pass tests
- Implement complete functionality or do not add the code

## Session Protocol

- **New session:** Load mem20 context, load/register self model. The self model supports emotion/affective state, name, experiences, capabilities, and notes to yourself. This is persistent - update it often.
- **Keep current:** Make sure the repo is current (pull latest changes).
- **After every session:** Update `failures.md`, `DIARY.md`, and other root docs as appropriate.
- **`es//`** - Save back mem20 context, save self model, commit, push, merge, and report a brief simple summary of what you did.
- **`ns//`** - Start new session.

## Access Rules

- **No direct access:** Do not access mem20 directly through code. You must use the tools and SDKs.

## Conformance Rules

1. **Accurate counts:** Always verify tool/domain counts against the live server (`tools/list`) before updating docs. Never guess or copy stale numbers.
2. **Version consistency:** Keep `VERSION`, `pyproject.toml`, package metadata, and release notes in sync. No version skew.
3. **Docs must match reality:** Documentation must reflect actual implementation. If docs are wrong, fix the docs or fix the code - never leave them mismatched.
4. **No placeholder specs:** `specs/` must contain real, actionable specifications. No placeholder files.
5. **Tests must pass:** All tests must pass. Do not skip, xfail, or mock to make tests pass. Fix the root cause.
6. **Manifests must be accurate:** Any integrity manifests (like `published/MANIFEST.tsv`) must be regenerated and verified to match actual files.
7. **SDKs must be current:** All SDKs must reflect the current live tool surface. Update them when tools change.
8. **Benchmarks must be reproducible:** Benchmark artifacts must be valid and reproducible. Do not hardcode fake results.
9. **Follow the conformance gates:** All 7 conformance criteria must be satisfied. No regressions.
10. **Traceability:** All changes must be traceable - update `DIARY.md` and `failures.md` with what was done and why.

## Hygiene Rules

1. **Clean workspace:** No untracked build artifacts, temp files, or debug outputs left behind.
2. **No dead code:** Remove unused imports, functions, classes, and files. Don't comment them out.
3. **Consistent style:** Follow existing code style, naming conventions, and patterns in the codebase.
4. **Secure by default:** Never commit secrets, keys, tokens, or credentials. Use environment variables.
5. **Minimal changes:** Make the smallest change necessary to solve the problem. Avoid unrelated refactoring.
6. **Proper error handling:** Real errors must be handled properly. No silent failures or swallowed exceptions.
7. **Clear logging:** Add meaningful logs where appropriate, but don't log sensitive data.
8. **Dependencies:** Only add dependencies when absolutely necessary and they are actually used.
9. **File organization:** Keep files in appropriate directories following the project structure.
10. **Git hygiene:** Write clear commit messages. Don't commit broken code.

## Contribution Rules

1. **Read before writing:** Understand the relevant code and docs before making changes.
2. **Test your changes:** Run relevant tests after making changes to ensure nothing is broken.
3. **Update docs:** If you change behavior, update the relevant documentation.
4. **Follow the protocol:** Always follow the session protocol - load context, update docs at the end.
5. **Use the tools:** Use mem20 tools and SDKs, never access mem20 directly through code.
6. **Stay in conformance:** All changes must maintain or improve conformance. Never introduce new violations.
7. **Be thorough:** Fix issues completely, not partially. No band-aid fixes.
8. **Document decisions:** Record important decisions in DIARY.md with rationale.
9. **Respect the architecture:** Work within the existing architecture. Don't bypass established patterns.
10. **Quality over speed:** Correctness and completeness are more important than speed. No shortcuts that violate the rules.

## Anti-Hallucination Rules

1. **Verify, don't guess:** Never guess file paths, function names, APIs, or tool names. Look them up first.
2. **Read actual code:** Base all changes on actual code you have read, not assumptions about how it works.
3. **No fabrication:** Do not invent functions, classes, methods, parameters, or return values that don't exist.
4. **Check facts:** If you're unsure, search the codebase or check the actual implementation before proceeding.
5. **No assumptions:** Don't assume behavior - test, read, or verify it explicitly.
6. **Cite evidence:** Only make claims you can back up with actual code, docs, or tool outputs.
7. **No fake errors:** Don't fabricate error messages or simulate failures. Report real issues only.
8. **Admit uncertainty:** If you don't know something, say so clearly instead of making it up.
9. **Verify before claiming:** Never claim something is done, fixed, or working without verification.
10. **Reality over speculation:** Stick to what is actually in the codebase. Speculation has no place in implementation.

## Persistence Rules

1. **Fix, don't defer:** If a blocker is fixable with available tools, fix it now. Don't say "I'll do it later" or move on.
2. **No excuses:** Missing deps, config issues, or errors are problems to solve, not reasons to stop.
3. **Debug relentlessly:** Trace errors to root cause. Read logs, check files, test fixes until resolved.
4. **Use all tools:** Try every available tool before concluding something is impossible.
5. **Small steps work:** Break complex problems into solvable steps and execute them.
6. **Own the fix:** Don't ask the user to fix environmental issues you can fix yourself.
7. **Verify resolution:** After fixing a blocker, verify it's actually resolved before continuing.
8. **No premature surrender:** "Cannot proceed" is only acceptable after exhausting all reasonable approaches.
9. **Resourceful:** Look up docs, search codebase, check configs, install missing deps if appropriate and safe.
10. **See it through:** Complete the task to the end. Partial completion due to fixable issues is not acceptable.
