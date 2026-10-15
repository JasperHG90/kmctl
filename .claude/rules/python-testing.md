---
name: Python Testing Rules
description: How to write, run, and locate tests in Python projects (pytest + uv). Read before adding or changing Python code.
paths: ["**/*.py"]
---

<constraint name="all-code-needs-tests">
Every code change ships with a test. You cannot claim code works or a
feature is done until a test exercises it and passes. For a bug fix, first
write a test that reproduces the bug, then make it pass.
</constraint>

## Running tests (your verify loop)

Run tests through `uv`, never a bare `pytest`: the bare interpreter may lack
the project environment. If the project defines task-runner recipes
(`justfile`, `Makefile`), prefer those, since they encode the blessed
invocation.

| Goal | Command |
|------|---------|
| Full default suite | `uv run pytest` |
| One directory | `uv run pytest tests/<area> -q` |
| One test | `uv run pytest tests/<area>/test_x.py::test_name` |

## Test tiers: don't wait on slow tests every round

Rerunning the whole suite after each edit spends most of the wait on tests
the edit cannot have broken. Split tests into tiers by cost with markers,
and run each tier at the stage that needs it.

<constraint name="mark-and-exclude-slow-tests">
A test that is expensive to run carries a marker that says what it costs,
and `addopts` in pyproject.toml leaves it out of the default run, so the
default `uv run pytest` stays fast and offline:

- `slow`: a local test that takes over about a second.
- `integration`: real external systems (network, databases, real tools).
- `llm`: paid or credentialed model APIs.

A topic marker (`api`, `db`) does not say whether a test is cheap to run,
so do not use one to pick tiers. Register every marker under `markers =`
and turn on `--strict-markers`, so a typo cannot slip a slow test back
into the default run.
</constraint>

<constraint name="measure-before-marking">
Find slow tests with `uv run pytest --durations=25` and mark the ones over
the threshold. Do not mark a test `slow` on a guess, and remove the marker
when a test gets fast again.
</constraint>

Use the project's task-runner recipe for a stage when it has one.

| Stage | Run |
|-------|-----|
| Each edit round | The tests nearest the change: `uv run pytest tests/<area> -x` |
| Fixing a failure | Only what failed last time: `uv run pytest --lf -x` |
| Before calling work done | The full default suite once, then each tier your change touches: `uv run pytest -m slow`, `-m integration` |

<constraint name="run-your-own-test">
A marker deselects a test even when you name it by path, so the test for
your change can silently not run. If it carries a tier marker, run it with
that marker: `uv run pytest tests/<area>/test_x.py::test_name -m slow`. A
`deselected` count in the summary means some tests did not run.
</constraint>

Things that trip people up:

- A `-m` on the command line replaces the `-m` in `addopts`; it does not
  add to it. `uv run pytest -m slow` runs only the slow tests. `-m ""`
  clears the filter and runs every tier; to run some tiers, write the
  whole expression, for example `-m "not llm"`.
- `--lf` with no cache, or after a run that passed, runs the full default
  selection.
- If `addopts` has `-n auto` (pytest-xdist), add `-n0` when running a few
  tests: starting the workers costs more than the tests.

<constraint name="every-tier-runs-somewhere">
A tier left out of the default run must still run before merge, usually in
CI. Say where it runs in the marker's description in pyproject.toml (for
example "off by default, CI runs it"). A tier that runs nowhere rots unseen.
</constraint>

<constraint name="tests-are-real-code">
Tests are linted and type-checked like the rest of the codebase (commonly
ruff and mypy). Before declaring work done, run the project's lint,
type-check, and test gates and make them pass. Never hide a failure with
`skip`, `xfail`, or `# type: ignore` to make a gate go green. Fix the cause
(see the pre-existing-issues rule).
</constraint>

## Where tests live

Mirror the source tree. Logic in `src/<pkg>/foo.py` is tested in
`tests/.../test_foo.py`. Name files `test_*.py` and functions `test_*`.
Keep shared fixtures in `conftest.py` at the narrowest level that serves the
tests using them (a suite-wide `tests/conftest.py`, or a subdir
`tests/<area>/conftest.py`). Keep reusable builders and factories in a plain
helper module (for example `tests/fixtures/`), separate from the test cases.

## Test isolation

<constraint name="test-isolation">
Each test is independent and must not rely on the state, order, or outcome
of another. A test that touches global state cleans up after itself.
</constraint>

Prefer pytest built-ins that clean up for you over manual teardown:

- `tmp_path` for files and directories (auto-removed).
- `monkeypatch` for env vars, attributes, and `cwd` (auto-reverted).
- An `autouse` fixture to reset shared or global state around each test.
- Choose the narrowest fixture `scope` that works (`function` by default).
  Widen to `module` or `session` only to share expensive setup, and only
  when the fixture holds no per-test mutable state.

<example name="redirect-global-state">
When the app reads global state (env vars, a user config or cache dir, a
database path), add an autouse fixture that redirects it into `tmp_path`,
for example `monkeypatch.setenv("APP_HOME", str(tmp_path / "home"))`, and
resets any cached singletons before and after each test. No test should read
or write real user directories.
</example>

## Mocking: run the real thing first

<constraint name="dont-mock-what-you-can-run">
Do not mock a dependency you can exercise for real cheaply. Mock only at
true external boundaries (network, paid or credentialed services).
Over-mocking yields tests that pass while production breaks.
</constraint>

- Filesystem and local tools: use real temp dirs and real local resources.
  For git, create a real local repo or bare remote under `tmp_path` instead
  of mocking the git layer.
- Database: point the app at a real, throwaway database under `tmp_path`
  (for example a temp SQLite file) rather than mocking the data layer.
- HTTP: mock with the library's community-standard tool, not hand-rolled
  patches and not live requests. For `httpx`, use respx.

<constraint name="check-mocking-capabilities">
Before adding any external mocking library, check whether the dependency
ships its own test support and whether the project already standardized on a
tool. Add a new dependency with `uv add` only when nothing existing fits.
</constraint>

## Writing good tests

- Assert observable behavior and outputs, not private implementation detail,
  so tests survive refactors.
- Make negative assertions precise. To assert a mock method was not called,
  use `assert mock.method_calls == []`, not `mock.assert_not_called()`. The
  latter only checks the mock was never called as a function, so it passes
  even when `mock.error(...)` fired.
- Cover many inputs with `@pytest.mark.parametrize`, not copy-pasted tests
  or a loop inside one test.
- For async tests, set `asyncio_mode = "auto"` (pytest-asyncio) so a plain
  `async def test_...` runs without a per-test decorator.
- Keep tests deterministic: no reliance on wall-clock time, ordering, real
  network, or unseeded randomness.

## TUI snapshot tests (Textual)

For a Textual TUI, use pytest-textual-snapshot. When a change intentionally
alters rendered output, review the snapshot diff, then refresh the baselines
with `uv run pytest <tui-tests> --snapshot-update`. Do not run
`--snapshot-update` just to clear a red test.
