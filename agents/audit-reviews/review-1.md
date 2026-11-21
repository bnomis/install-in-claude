# Audit Review 1

**Date:** 2026-11-21
**Scope:** full (`agents/specs/`, `src/`, `bin/`, `AGENTS.md`, `README.md`; there is no `docs/`)
**Commit:** e3ce2a2f8e307ba3162134592560c1d1c8f447c8
**Script output:** /tmp/audit-install-in-claude.jsonl (7 hits, 0 accepted, 7 unaccepted)
**Convergence note:** first audit of this project: no previous review, so every
sampled question ran on the whole tree, and every listed question (A1, A4,
A11, A17, A19, T1, T2, Doc1, Doc2, Doc4, Doc5) judged every candidate as new.
Every finding below is catch-up, not a regression. Checker digest
`e924b332c5c6809821c1635aa7a1d3714064120de0317c733f7f09dfa6b50537`.
**Review page:** https://claude.ai/artifact/54NcHjtmRvMeM7fNSLwigC

## What is being reviewed and how

The first audit of `install-in-claude`, the command that links a project's
Claude Code files into `~/.claude/` and merges its `settings.json` entries.
Each item below is a change proposed to clear a finding: approve it or flag
it. Two findings contradict a choice the spec made, so they are decisions:
pick an option for each. Nothing is changed until every item and decision has
an answer.

## Automatic checks

| Check | Result |
|---|---|
| `requests.md` `## Open` empty at audit start | pass |
| Mechanical sweep (`checks/audit.py`) ran, output saved | pass: 7 unaccepted hits, listed below |
| `ruff-version-drift` (ruff in `.venv` vs `ruff-pre-commit` rev) | pass: no hit |
| Lockfile drift (D3) | pass: no hit |
| Every listed batch passed `phaseb.py check` and was merged | pass |
| Spec against the specdev validation criteria | pass: every template section present, API has typed signatures, links resolve |

## Summary

The sweep reported `except-interpolation` 3 times and `literal-duplication`
4 times (two pairs), all low severity. Phase B found 7 sites for A1 (external
call envelope), 2 for Sec2 (input validation), 1 for A17 (public surface) and
2 spec drifts for Doc4 (one of them reported under two candidate ids). Every
other question returned no hits.

## Mechanical findings (from checks/audit.py)

### Rule: except-interpolation - f-string interpolates caught exception

- **Severity:** low
- **Instance count:** 3
- **Locations:**
  - `src/install_in_claude/cli.py:102` - `print(f'ERROR: {e}', file=sys.stderr)`
  - `src/install_in_claude/cli.py:105` - `print(f'ERROR: {e}', file=sys.stderr)`
  - `src/install_in_claude/settings.py:66` - `raise EditError(f'{option} {text!r}: the value is not valid JSON ({e})') from e`
- **Recommendation:** accept each with a scoped marker. At `cli.py:102,105`
  the domain error's message is the whole of the user-facing report, by
  design (spec, Error handling). At `settings.py:66` the JSON parser's
  position is the only place the user learns where the value broke, because
  `main()` prints `str(e)`, not the chained cause.
  `# auditme: accept[except-interpolation] <reason>`.

### Rule: literal-duplication - identical ordered literal across 2 locations

- **Severity:** low
- **Instance count:** 4 (two pairs)
- **Locations:**
  - `src/tests/test_cli.py:99` - `('settings.json',)` (also `src/tests/test_settings.py:203`)
  - `src/tests/test_settings.py:203` - `('settings.json',)` (also `src/tests/test_cli.py:99`)
  - `src/tests/test_settings.py:20` - `('hooks', 'Stop')`
  - `src/tests/test_settings.py:25` - `('hooks', 'Stop')`
- **Recommendation:** accept each with
  `# auditme: accept[literal-duplication] expected value written out in an assertion`.
  Each is the expected value of a separate test. A shared constant would
  hide what the test asserts.

## Phase B per-question results

Listed questions name their candidates. Every sampled question ran in full
mode, because there is no previous review `**Commit:**`.

### A1 (listed): External call envelope

- **Candidates judged:** 7, every one; none left unjudged.
- **Hits:**
  - `src/install_in_claude/links.py:38` - `target.mkdir` lets `OSError` escape untranslated
  - `src/install_in_claude/links.py:47` - `dest.mkdir` lets `OSError` escape untranslated
  - `src/install_in_claude/links.py:22` - `dst.unlink` in `link_one`; neither caller in `link_entries` (lines 44, 48) wraps it
  - `src/install_in_claude/links.py:25` - `dst.symlink_to` in `link_one`, same
  - `src/install_in_claude/settings.py:183` - `path.read_text` sits before the `try`, which covers `json.loads` alone
  - `src/install_in_claude/settings.py:203` - `path.parent.mkdir` sits before the `try` at line 205
  - `src/install_in_claude/settings.py:212` - clean-up `unlink` in an `except BaseException` that only re-raises
### A2 (sampled): Except tuple coverage - mode full - no hits (1 file had a matching `try`)
### A3 (sampled): Domain-error layering - mode full - no hits
### A4 (listed): Docstring `Raises` accuracy - 8 candidates judged, every one - no hits
### A5 (sampled): Two sources of truth - mode full - no hits
### A6 (sampled): Stage method dual-path - mode full - no hits (no matching construct)
### A7 (sampled): Constructor purity - mode full - no hits
### A8 (sampled): Late dataclass mutation - mode full - no hits
### A9 (sampled): Pure-named function side effects - mode full - no hits
### A10 (sampled): Predicate semantics - mode full - no hits (no matching construct)
### A11 (listed): Exhaustion via assert_never - no candidates in the tree - no hits
### A12 (sampled): assert misuse - mode full - no hits (no `assert` outside tests)
### A13 (sampled): Same value to multiple slots - mode full - no hits
### A14 (sampled): Repeated computation per request - mode full - no hits
### A15 (sampled): Duplicate constructor logic - mode full - no hits
### A16 (sampled): CLI entry envelope - mode full - no hits (`main` has no `raise` outside its `try`)

### A17 (listed): Public-surface drift

- **Candidates judged:** 1, every one.
- **Hits:**
  - `src/install_in_claude/__init__.py:17` - `__all__` re-exports 14 names that nothing outside the package reads; only `main` is reached, through the `pyproject.toml` entry point `install_in_claude.cli:main`

### A18 (sampled): Hot-path setup - mode full - no hits (no callbacks)
### A19 (listed): Logger level for broad-except - 1 candidate judged (`settings.py:211`, cleans up and re-raises) - no hits
### A20 (sampled): Mutable module-level singleton - mode full - no hits (`ACTIONS`, `UNCHANGED` and `__all__` are read by no other module; grep covered all three forms across `src/`)
### A21 (sampled): Lazy init race - mode full - no hits
### A22 (sampled): Fall-through after partial handling - mode full - no hits
### A23 (sampled): Discarded multi-return - mode full - no hits
### A24 (sampled): Subprocess memoisation - mode full - no hits (no subprocess)
### A25 (sampled): Shallow immutable wrapper - mode full - no hits
### S1 (sampled): Type annotations - mode full - no hits; tests: 0 missing parameter, 0 missing return annotations, 0 modules affected, 4 modules fully annotated (`conftest.py` is empty)
### S2 (sampled): Naming conventions - mode full - no hits
### S3 (sampled): TYPE_CHECKING placement - mode full - no hits (no such block)
### S4 (sampled): Project rule files - mode full - no hits (AGENTS.md references no rule file)
### P1-P3 (sampled): Performance - mode full - no hits
### Sec1 (sampled): Secrets in source - mode full - no hits
### Sec2 (sampled): Input validation at system boundaries

- **Mode:** full
- **Hits:**
  - `src/install_in_claude/cli.py:70` - a `--target` that is an existing file is not refused; `target.mkdir` (`links.py:38`) raises `FileExistsError` and the user gets a traceback (reproduced: exit 1, traceback)
  - `src/install_in_claude/cli.py:71` - a `--settings` that is a directory is not refused; `read_settings` raises `IsADirectoryError` (reproduced: exit 1, traceback)

### Sec3-Sec5 (sampled) - mode full - no hits (no subprocess; the printed `rm` line is `shlex.quote`d; no logging)
### T1 (listed): Coverage of branchy logic - 12 candidates judged, every one - no hits
### T2 (listed): Property-based tests - no candidates in the tree - no hits
### T3 (sampled): Integration balance - mode full - no hits (`test_cli.py` runs `main` end to end)
### D1-D3 (sampled) - mode full - no hits (`ruff` is run by the `ruff-pre-commit` hooks)
### Doc1, Doc2 (listed) - 3 and 2 candidates judged, every one - no hits
### Doc3 (sampled) - mode full - no hits

### Doc4 (listed): Specs match implementation

- **Candidates judged:** 48, every one.
- **Hits:**
  - `agents/specs/install-in-claude/spec.md:147` - says the message for a `settings.json` that is not an object names `python3 -m json.tool <file>`; `settings.py:189` gives no such hint (only the invalid-JSON message at `settings.py:187` does)
  - `agents/specs/install-in-claude/spec.md:235-236` - names the `no-project-names` hook's repository as `git@github.com:bnomis/agents.git`; `.pre-commit-config.yaml:12` takes it from `git@github.com:bnomis/auditor.git` since commit `e3ce2a2` (reported under two candidate ids, one finding)

### Doc5 (listed): User docs match implementation - 7 candidates judged, every one - no hits

### Coverage (sampled)

The Sec2 sites are the only new sites from sampled questions; on a first
audit everything is catch-up.

### Brief thresholds the reviewers raised

None changed a verdict; recorded so the next audit applies the same reading.

- A17: an entry point naming `install_in_claude.cli:main` was counted as a use of `main`, not as a bypass of the package surface.
- T1: the test index did not follow calls through the `run()` and `apply()` test helpers; the reviewer counted them as direct calls.
- Doc4: the wording of an error message was counted as part of "errors raised" (decides the `spec.md:147` hit).
- Doc5: the README options table leaving out cappa's own `--help` and `--completion` was not counted as drift.
- Doc1: a path outside the repository (`~/.claude/settings.json`) was not counted as stale.

## Phase B findings (consolidated)

### Finding: filesystem errors reach the user as tracebacks

- **Category:** A, Sec
- **Question:** A1, Sec2
- **Severity:** medium
- **Location:** `links.py:22,25,38,47`, `settings.py:183,203,212`, `cli.py:70,71`
- **Description:** no `OSError` is translated to a domain error. The spec
  chooses this for linking and writing ("An `OSError` while linking or
  writing: traceback, propagates", `spec.md:151`), but the reading of
  `settings.json` and the two option mistakes above happen before anything
  changes, and the spec does not cover them.
- **Recommendation:** decision D1 below.

### Finding: the package re-exports names nothing reads

- **Category:** A
- **Question:** A17
- **Severity:** low
- **Location:** `src/install_in_claude/__init__.py:1-33`
- **Description:** the spec's Module location table (`spec.md:30`) says
  `__init__.py` re-exports the public API, but the tool is consumed only as a
  command, and the tests import from the submodules.
- **Recommendation:** decision D2 below.

### Finding: spec names the old repository for the names hook

- **Category:** Doc
- **Question:** Doc4
- **Severity:** low
- **Location:** `agents/specs/install-in-claude/spec.md:235-236`
- **Description:** see Doc4 above.
- **Recommendation:** name `git@github.com:bnomis/auditor.git`, the auditor
  repository, as `.pre-commit-config.yaml` does.

### Finding: spec promises a `json.tool` hint for a non-object settings file

- **Category:** Doc
- **Question:** Doc4
- **Severity:** low
- **Location:** `agents/specs/install-in-claude/spec.md:147`
- **Description:** see Doc4 above.
- **Recommendation:** amend the spec, not the code: `json.tool` finds a
  syntax error, and a file that is valid JSON but not an object parses
  cleanly, so the hint would not help. Split the row: invalid JSON names the
  file and `json.tool`; not an object names the file.

## Items

| Id | Change | Recommendation |
|---|---|---|
| I1 | Scoped `except-interpolation` markers at `cli.py:102,105` | approve |
| I2 | Scoped `except-interpolation` marker at `settings.py:66` | approve |
| I3 | Scoped `literal-duplication` markers at the four test sites | approve |
| I4 | Spec `spec.md:235-236`: name the auditor repository | approve |
| I5 | Spec `spec.md:147`: split the row; `json.tool` only for invalid JSON | approve |

## Decisions

### D1. How the command reports filesystem errors

- **What is being decided:** whether an `OSError` keeps reaching the user as
  a traceback, at each of the A1 and Sec2 sites.
- **Background:** the spec (2026-11-21) lets an `OSError` while linking or
  writing propagate, following the coding standard's "let unexpected
  exceptions propagate": a traceback is the most useful report of a failure
  nobody foresaw, and `settings.json` is written last and atomically, so it
  stays intact. The spec does not cover reading `settings.json`, or the two
  option mistakes (a `--target` that is a file, a `--settings` that is a
  directory), which fail before anything changes and are foreseeable.
- **What it affects:** `cli.py`, `settings.py`, the spec's Error handling
  table, the README's Exit codes table, and tests in `test_cli.py` and
  `test_settings.py`.
- **Options:**
  - **A (recommended): check up front, keep propagation for the rest.**
    `install()` refuses a `--target` that exists and is not a directory, and
    a `--settings` that exists and is not a file, with exit 2 and a message,
    as it already does for `--source`. `read_settings` translates `OSError`
    and `UnicodeDecodeError` to `SettingsError` (exit 1, "cannot read"). The
    A1 sites in `links.py` and `write_settings` stay as the spec has them and
    are dismissed with the reason "spec: an OSError while linking or writing
    propagates". Spec and README updated.
  - **B: translate every `OSError`.** Every filesystem call is wrapped and
    raised as an `InstallError` with a message, exit 1; no traceback is ever
    shown. Clears every A1 site, but a permission or disk failure loses its
    traceback, and the spec's propagation rule is reversed.
  - **C: keep the spec as it is.** Dismiss every A1 site and accept the two
    Sec2 sites; both option mistakes keep ending in a traceback.

### D2. The package's re-exports

- **What is being decided:** whether `src/install_in_claude/__init__.py`
  keeps re-exporting the API.
- **Background:** the spec (2026-11-21) lists the API with signatures, as
  the specdev template asks, and its Module location table says
  `__init__.py` re-exports it. Nothing reads the re-exports: the tool is
  installed and run with `uvx` or `uv tool install`, and the tests import
  from `cli`, `links` and `settings` directly.
- **What it affects:** `src/install_in_claude/__init__.py`, the spec's
  Module location row (`spec.md:30`).
- **Options:**
  - **A (recommended): drop the re-exports.** `__init__.py` becomes empty
    (or a docstring); the spec row says the package is the command. Removes
    a list that has to be kept in step with every rename.
  - **B: keep them as a library API.** The A17 finding is dismissed with the
    reason "the API is published for import"; the list stays to be
    maintained.

## Files reviewed (Phase B)

- `src/install_in_claude/__init__.py` - A1-A25, S1-S4, P1-P3, Sec1-Sec5, T1-T3, D1, Doc4
- `src/install_in_claude/cli.py` - same
- `src/install_in_claude/links.py` - same
- `src/install_in_claude/settings.py` - same
- `src/tests/conftest.py`, `src/tests/test_cli.py`, `src/tests/test_links.py`, `src/tests/test_settings.py` - A1-A25, S1-S3, T1-T3
- `bin/activate.sh`, `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml` - Sec1, D1-D3, Doc1, Doc2, Doc4
- `AGENTS.md`, `README.md` - Doc1-Doc3, Doc5
- `agents/specs/install-in-claude/spec.md`, `agents/specs/install-in-claude/rollout.md` - Doc4, spec review

## Prior findings re-verified

None: this is the first review, and there are no audit task lists.

## Recommendations

1. D1 (medium): decide how filesystem errors are reported; option A.
2. I1-I3: add the scoped accept markers.
3. I4, I5: correct the spec.
4. D2: drop the unused re-exports.

## Answers

Answered on the review page, 2026-11-21. No comments were left.

| Id | Answer |
|---|---|
| I1 | approve |
| I2 | approve |
| I3 | approve |
| I4 | approve |
| I5 | approve |
| D1 | A: check `--target` and `--settings` up front (exit 2), translate read failures in `read_settings` to `SettingsError`, keep propagation for linking and writing; dismiss those A1 sites with that reason |
| D2 | A: drop the re-exports; the spec says the package is the command |
