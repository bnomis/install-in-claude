# Rollout of install-in-claude

**Date:** 2026-11-21

The order of work for replacing each project's copy of `bin/install-claude.py`
with [install-in-claude](spec.md). Each step is its own spec or amendment in
the repository it changes, and that amendment names its own files and
arguments; this note names no project.

1. **This repository.** Implement [spec.md](spec.md); create the private
   GitHub repository `bnomis/install-in-claude` and push `main`. The commit
   pushed is the one every project pins.
2. **Each project that uses a copy**, one at a time, the project with the most
   involved `settings.json` edit (an `--append` with a `MATCH`) first:
   - replace `bin/install-claude.py` with `bin/install-claude.sh`, which runs
     the pinned commit with `--source` and the project's own options (see the
     spec's [Consumers](spec.md#consumers));
   - remove the copy's own tests and any accept markers that existed only
     for it;
   - update the project's user guide wherever it names `bin/install-claude.py`.
3. **Check each switch** by running the new wrapper with `--dry-run`, then for
   real, and comparing `~/.claude` and `~/.claude/settings.json` with what the
   old copy produced: no link changed, no settings change.
