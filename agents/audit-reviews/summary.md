# Audit Summary

**Last updated:** 2026-11-21
**Last review:** review-1
**Total reviews conducted:** 1
**Last script run hit count:** 7 (0 accepted)
**Script version:** e924b332c5c6809821c1635aa7a1d3714064120de0317c733f7f09dfa6b50537

## Unresolved findings

### Filesystem errors reach the user as tracebacks

- **Rule or category:** A1, Sec2
- **Severity:** medium
- **Location:** `src/install_in_claude/links.py:22,25,38,47`, `src/install_in_claude/settings.py:183,203,212`, `src/install_in_claude/cli.py:70,71`
- **First raised:** review-1 (2026-11-21)
- **Description:** no `OSError` is translated; a `--target` that is a file or a `--settings` that is a directory ends in a traceback.
- **Recommendation:** review-1 decision D1.

### The package re-exports names nothing reads

- **Rule or category:** A17
- **Severity:** low
- **Location:** `src/install_in_claude/__init__.py:17`
- **First raised:** review-1 (2026-11-21)
- **Description:** `__all__` lists names no consumer reads.
- **Recommendation:** review-1 decision D2.

### Spec drift: names-hook repository and json.tool hint

- **Rule or category:** Doc4
- **Severity:** low
- **Location:** `agents/specs/install-in-claude/spec.md:147`, `agents/specs/install-in-claude/spec.md:235-236`
- **First raised:** review-1 (2026-11-21)
- **Description:** the spec names the agents repository for the names hook (it is the auditor repository), and promises a `json.tool` hint for a non-object settings file.
- **Recommendation:** amend the spec (review-1 items I4, I5).

### except-interpolation

- **Rule or category:** `except-interpolation`
- **Severity:** low
- **Location:** `src/install_in_claude/cli.py:102,105`, `src/install_in_claude/settings.py:66`
- **First raised:** review-1 (2026-11-21)
- **Description:** caught exception interpolated into a message.
- **Recommendation:** scoped accept markers (review-1 items I1, I2).

### literal-duplication in tests

- **Rule or category:** `literal-duplication`
- **Severity:** low
- **Location:** `src/tests/test_cli.py:99`, `src/tests/test_settings.py:20,25,203`
- **First raised:** review-1 (2026-11-21)
- **Description:** the same expected value written out in two assertions.
- **Recommendation:** scoped accept markers (review-1 item I3).

## Recently resolved

| Finding | Severity | Raised in | Resolved in |
|---------|----------|-----------|-------------|

## Recurring patterns

- (none yet: first review)

## Checker changes since the last review

- (none: first review)
