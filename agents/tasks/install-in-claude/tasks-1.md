# Tasks: install-in-claude

**Spec:** `agents/specs/install-in-claude/spec.md`
**Created:** 2026-11-21
**Version:** 1

The repository is new: Task 1 creates the files every later task's Definition
of Done runs (`bin/activate.sh`, the pre-commit hooks, the test layout). The
modules replace copies of one script that lived in several projects; Task 7
checks that no helper is written twice. Creating the GitHub repository and
pushing are not tasks here: they are the operator's step 1 of
`agents/specs/install-in-claude/rollout.md`, after this list.

---

## Task 1: Scaffold the repository

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** Module location, Repository, External dependencies

**Technical Goal:** Give the repository its project files, hooks and empty
package, so every later task has the checks its Definition of Done names.

**Subtasks:**

- [x] Check the starting point: `src/install_in_claude/` does not exist, and
      `git log` holds no commit touching `src/`; if either fails, stop the
      list as `blocked`, naming what exists
- [x] `pyproject.toml`: `name = "install-in-claude"`, `version = "0.1.0"`,
      `requires-python = ">=3.14"`, `dependencies = ["cappa>=0.33.0"]`,
      `[project.scripts] install-in-claude = "install_in_claude.cli:main"`,
      a hatchling build with `packages = ["src/install_in_claude"]`, dev
      group `pytest>=9.2.0` and `ruff==0.17.4`, and `[tool.ruff]` with
      `line-length = 160`, `quote-style = "single"`, lint `select = ["B",
      "E", "F", "I", "ICN", "S", "SIM", "TID"]`, `ignore = ["E501", "SIM108"]`, and
      `"src/tests/*" = ["S101"]` under per-file ignores
- [x] `uv lock`, then `uv sync`; `uv.lock` resolves cappa 0.33.0 and ruff
      0.17.4 (ruff 0.17.4 was released 2026-11-05, outside the 14-day
      `exclude-newer` window)
- [x] `bin/activate.sh`: sources `.venv/bin/activate` and prepends `src` to
      `PYTHONPATH`, resolved from the script's own directory
- [x] `.gitignore`: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`,
      `.pytest_cache/`, `.ruff_cache/`
- [x] `.pre-commit-config.yaml`: `astral-sh/ruff-pre-commit` at `rev: v0.17.4`
      with `ruff-check` and `ruff-format`; `git@github.com:bnomis/agents.git`
      at `rev: 0394f33ad0a93344a9d387a399225c0dca94a955` with
      `id: no-project-names` and `args: [--allow=install-in-claude]`
- [x] `pre-commit install --hook-type pre-commit --hook-type pre-push
      --hook-type commit-msg`
- [x] `AGENTS.md`: what the repository is, the test command
      (`source bin/activate.sh && pytest src/tests -q`), and a "No project
      names" section: the repository serves many projects and names none it
      was run on in code, tests, fixtures, specs, records or commit messages;
      the `no-project-names` hook enforces it
- [x] `CLAUDE.md` holding `@AGENTS.md`
- [x] `src/install_in_claude/__init__.py` (empty `__all__`) and
      `src/tests/conftest.py` (empty)
- [x] Commit the spec, the rollout note, both indexes, this task list and the
      scaffold as `build: scaffold install-in-claude`

**Acceptance Criteria:**

- [x] `source bin/activate.sh && python -c 'import install_in_claude'` exits 0
- [x] `source bin/activate.sh && ruff --version` prints `ruff 0.17.4`
- [x] `pre-commit run --all-files` exits 0

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pre-commit run --all-files` exits 0

**Notes:**

- The names hook's `rev` is the one the other shared repositories pin as of
  2026-11-21; the hook reads its list from outside every repository.

---

## Task 2: Parse the settings edits

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** API (settings.py), Edits to `settings.json`, Error handling

**Technical Goal:** Turn each `--set-if-absent` and `--append` argument into
a `SetIfAbsent` or `Append`, refusing every malformed one before anything is
touched.

**Subtasks:**

- [x] In `src/install_in_claude/settings.py`: `InstallError(Exception)`,
      `EditError(InstallError)`, `SettingsError(InstallError)`, the frozen
      dataclasses `SetIfAbsent(path, value)` and `Append(path, value, match)`
- [x] `parse_set_if_absent(text)` and `parse_append(text)`: split `PATH` (and
      for `--append`, an optional `[MATCH]`) from `JSON` at the first `=`
      after them, with `^([^.\[\]=]+(?:\.[^.\[\]=]+)*)(\[[^\]]+\])?=(.*)$`
      (DOTALL); `[MATCH]` is refused by `parse_set_if_absent`; the value is
      `json.loads` of the rest
- [x] Each `EditError` message names the argument as given and what is wrong:
      no `=`, empty or invalid `PATH`, `[]` with no `MATCH`, invalid JSON
- [x] `src/tests/test_settings.py`: each valid form (one part, dotted, with
      `MATCH`, a value holding `=` and `]`), and each error

**Acceptance Criteria:**

- [x] `parse_append('hooks.Stop[auditme-stop.sh]={"a":1}')` returns
      `Append(('hooks', 'Stop'), {'a': 1}, 'auditme-stop.sh')`
- [x] `parse_set_if_absent('statusLine={"type":"command"}')` returns
      `SetIfAbsent(('statusLine',), {'type': 'command'})`
- [x] Every malformed form raises `EditError`

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_settings.py -q` exits 0

**Notes:**

- Depends on Task 1
- Key file: `src/install_in_claude/settings.py`

---

## Task 3: Apply the edits

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** API (`apply_edits`), Edits to `settings.json`, Error handling

**Technical Goal:** Merge the edits into a settings object, purely, with one
message per edit.

**Subtasks:**

- [x] `apply_edits(settings, edits)`: work on a deep copy; walk each `path`,
      creating missing objects; `SetIfAbsent` sets only a missing key;
      `Append` creates a missing list, and skips when an element equals the
      value (no `match`), or when an element's
      `json.dumps(element, sort_keys=True, separators=(',', ':'))` contains
      `match`
- [x] `SettingsError` naming the dotted path and the type found when a part
      on the way is not an object, or an `--append` target is not a list
- [x] Return the new object and the messages (`set` / `already set` /
      `appended` / `already has a matching entry`, each naming the path);
      one `EditOutcome` per edit (path, kind, changed), whose `message(settings_path, dry_run)` words it
- [x] Tests in `src/tests/test_settings.py`: set when absent, kept when
      present (whatever the value); append to a missing list, beside other
      entries, skipped on an equal element, skipped on a `MATCH` (an entry
      `{"hooks":[{"command":"bash /elsewhere/auditme-stop.sh"}]}`), not
      skipped when `MATCH` is absent; wrong types refused; edits applied in
      order; the input object is not mutated

**Acceptance Criteria:**

- [x] Each case above passes
- [x] `apply_edits` reads and writes no file

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_settings.py -q` exits 0

**Notes:**

- Depends on Task 2

---

## Task 4: Read and write `settings.json`

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** API (`read_settings`, `write_settings`), Error handling

**Technical Goal:** Read the file safely and write it atomically, keeping its
mode and the first original.

**Subtasks:**

- [x] `read_settings(path)`: `{}` when absent; `SettingsError` naming the file
      and `python3 -m json.tool <file>` when it is not valid JSON, and naming
      the file when it is not an object
- [x] `write_settings(path, settings)`: copy an existing file to
      `settings.json.orig` only if no `.orig` exists; create the parent; write
      `json.dumps(settings, indent=2) + '\n'` to a temporary file in the same
      directory, copy the old mode onto it, `os.replace`; remove the temporary
      file on any failure and re-raise
- [x] Tests: absent file read as `{}`; invalid JSON and a JSON array refused,
      file unchanged, no `.orig`; written file round-trips; mode `0o600` kept;
      `.orig` written once across two writes; no temporary file left after a
      write

**Acceptance Criteria:**

- [x] Each case above passes

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_settings.py -q` exits 0

**Notes:**

- Depends on Task 2 (the error classes)

---

## Task 5: Link the entries and report dangling links

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** API (links.py), Implementation steps 4 and 5

**Technical Goal:** Link a source tree into a target exactly as the copies
did, with a dry-run mode, and find dangling links.

**Subtasks:**

- [x] `link_entries(source, target, dry_run)`: create `target`; for each
      top-level entry of `source` not starting with `.`, in sorted order, link
      a file as `target/<name>`, or for a directory create `target/<name>` and
      link each of its entries (sorted, dotfiles included) into it
- [x] For each link: replace a link in the way; rename a real file in the way
      to `<name>.orig`, then `<name>.orig.2` and on; link relatively
      (`src.parent.relative_to(dst.parent, walk_up=True) / src.name`);
      return `Linking <src> to <dst> via <relative>`, or `Would link ...`
      with nothing changed when `dry_run`
- [x] `dangling_links(target, max_depth=2)`: walk `target`, not below
      `max_depth`, returning each symlink whose target is gone, sorted
- [x] `src/tests/test_links.py`: a new file; an existing link replaced; a real
      file renamed `.orig` then `.orig.2`; directories linked one level down;
      top-level dotfiles skipped; a second run changes nothing; dry run
      changes nothing; a dangling link found; none when all resolve; none
      below `max_depth`

**Acceptance Criteria:**

- [x] Each case above passes
- [x] Every link made is relative

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_links.py -q` exits 0

**Notes:**

- Depends on Task 1
- Key file: `src/install_in_claude/links.py`

---

## Task 6: The command

**Status:** todo
**Priority:** high
**Complexity:** medium
**Spec Reference:** API (cli.py), Implementation, Settings, Error handling, Consumers

**User Story:** As a project maintainer, I want one command that links my
project's Claude files and merges its settings from arguments, so that no
project keeps its own copy of the installer.

**Subtasks:**

- [ ] `src/install_in_claude/cli.py`: the `InstallInClaude` cappa dataclass
      with the options in the spec's Settings table, and `main(argv)`
- [ ] `main` in the spec's order: parse the edits (`EditError` -> stderr,
      exit 2); resolve `--source` and refuse a non-directory
      (`ERROR: <source> is not a directory`, exit 2); default `--target` to
      `~/.claude` (expanded) and `--settings` to `<target>/settings.json`;
      read and apply the edits in memory (`SettingsError` -> stderr, exit 1,
      before any link); link and print; print each dangling link and one
      `rm ...` line; write the settings only if they changed (not with
      `--dry-run`, which prints `Would set` / `Would append`); print each
      edit's message; return 0
- [ ] Re-export the public API from `src/install_in_claude/__init__.py` with
      `__all__`
- [ ] `src/tests/test_cli.py`, each in a temporary target and settings file:
      the three invocations in the spec's Consumers table end to end, each
      twice (the second run changes nothing); `--dry-run` changes nothing;
      an invalid edit exits 2 with nothing linked; a missing source exits 2;
      an invalid `settings.json` exits 1 with nothing linked and the file
      unchanged; a dangling link is reported with its `rm` line

**Acceptance Criteria:**

- [ ] Each case above passes
- [ ] `source bin/activate.sh && install-in-claude --help` lists every option
      in the spec's Settings table

**Definition of Done:**

- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `source bin/activate.sh && pytest src/tests/test_cli.py -q` exits 0

**Notes:**

- Depends on Tasks 3, 4 and 5
- Key file: `src/install_in_claude/cli.py`

---

## Task 7: User guide, duplication check and close the spec

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** Repository, Testing, Consumers

**User Story:** As a project maintainer, I want a guide with copy-paste
invocations, so that switching a project to the tool needs nothing else.

**Subtasks:**

- [ ] `README.md`: what it is and why; install and run with
      `uvx --from "git+ssh://git@github.com/bnomis/install-in-claude.git@<commit>" install-in-claude ...`
      (the commit from `git ls-remote git@github.com:bnomis/install-in-claude.git refs/heads/main`),
      or `uv tool install` for one machine; the options table; the three
      consumer invocations as examples; the `[MATCH]` form and why it exists;
      `--dry-run`; exit codes; why `--source` has no default
- [ ] Hoist anything the modules duplicate to a single owner: grep
      `src/install_in_claude/` for each literal collection, constant and
      one-line helper the modules define, and import rather than copy
- [ ] `uvx --from . install-in-claude --help` from the repository root exits 0
- [ ] Set the spec's `**Status:**` to `implemented`, and update
      `agents/specs/index.md` if its description no longer matches

**Acceptance Criteria:**

- [ ] Every option in the spec's Settings table appears in `README.md`
- [ ] No helper or constant is defined twice in `src/install_in_claude/`

**Definition of Done:**

- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pre-commit run --all-files` exits 0
- [ ] `source bin/activate.sh && pytest src/tests -q` exits 0

**Notes:**

- Depends on Task 6
- The GitHub repository and the push are the operator's, after this task
  (rollout step 1); the README's `git ls-remote` command works once they exist.
