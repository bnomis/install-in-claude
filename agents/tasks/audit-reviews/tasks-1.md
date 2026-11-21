# Tasks: Audit Review 1

**Source:** `agents/audit-reviews/review-1.md`
**Created:** 2026-11-21
**Version:** 1

Applies the answers recorded in the review's Answers section (2026-11-21):
items I1-I5 approved, option A for D1 (filesystem errors) and option A for D2
(re-exports). Each task reads what it applies from that section, not from the
review page.

---

## Task 1: Accept the deliberate sweep hits

**Status:** done
**Priority:** low
**Complexity:** small
**Source Reference:** review-1 items I1, I2, I3 (rules `except-interpolation`, `literal-duplication`)

**Technical Goal:** Mark the seven sweep hits that the review judged
deliberate, with markers scoped to their rule, so the sweep reports them as
accepted.

**Subtasks:**

- [x] Confirm review-1's Answers section approves I1, I2 and I3; if it does not, stop the task as `blocked`, naming the missing answer
- [x] On `src/install_in_claude/cli.py` lines `print(f'ERROR: {e}', file=sys.stderr)` in both `except` blocks of `main()`, add `# auditme: accept[except-interpolation] the domain error's message is the report the user sees`
- [x] On the `raise EditError(... the value is not valid JSON ({e})) from e` line of `parse_edit` in `src/install_in_claude/settings.py`, add `# auditme: accept[except-interpolation] main() prints str(e), so the parser's position reaches the user only here`
- [x] On the four `literal-duplication` sites (`src/tests/test_cli.py`, the `('settings.json',)` assertion in `test_invalid_settings_exit_1_with_nothing_linked`; `src/tests/test_settings.py`, the `('hooks', 'Stop')` assertions in `test_append_parses_a_match` and `test_append_without_a_match` and the `['settings.json']` assertion in `test_a_new_file_gets_no_original`), add `# auditme: accept[literal-duplication] expected value written out in an assertion` on the line or the line above

**Acceptance Criteria:**

- [x] `python3 ~/.claude/skills/auditme/checks/audit.py .` prints no line with `"accepted": false` for `except-interpolation` or `literal-duplication`
- [x] Every marker is scoped (`accept[<rule>]`), none unscoped

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_cli.py src/tests/test_settings.py -q` passes

**Notes:**

- Key files: `src/install_in_claude/cli.py`, `src/install_in_claude/settings.py`, `src/tests/test_cli.py`, `src/tests/test_settings.py`
- Find each site by its text, not by the line numbers in the review: later tasks move lines

---

## Task 2: Correct the two spec drifts

**Status:** done
**Priority:** low
**Complexity:** small
**Source Reference:** review-1 items I4, I5 (Doc4)

**Technical Goal:** Bring `agents/specs/install-in-claude/spec.md` in line
with the code on the two points the audit found.

**Subtasks:**

- [x] Confirm review-1's Answers section approves I4 and I5; if it does not, stop the task as `blocked`, naming the missing answer
- [x] In the Repository section, replace the names hook's repository `git@github.com:bnomis/agents.git` with `git@github.com:bnomis/auditor.git`, the auditor repository, as `.pre-commit-config.yaml` has it; keep the rest of the sentence true (read it against `.pre-commit-config.yaml`)
- [x] In the Error handling table, split the row "`settings.json` is not valid JSON, or not an object" into two: not valid JSON gives a message naming the file and `python3 -m json.tool <file>`; not a JSON object gives a message naming the file

**Acceptance Criteria:**

- [x] `grep -n 'agents.git' agents/specs/install-in-claude/spec.md` prints nothing
- [x] The spec's not-an-object row matches the message `read_settings` raises (`<path> is not a JSON object; not changed`)

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Key file: `agents/specs/install-in-claude/spec.md`
- Documentation only; no test changes

---

## Task 3: Drop the package's re-exports

**Status:** done
**Priority:** low
**Complexity:** small
**Source Reference:** review-1 decision D2 (A17)

**Technical Goal:** Remove the unused `__all__` surface from
`src/install_in_claude/__init__.py`, as D2 option A decided, and say in the
spec that the package is the command.

**Subtasks:**

- [x] Confirm review-1's Answers section records D2 as A; if it does not, stop the task as `blocked`, naming the missing answer
- [x] Check that nothing imports a name from the package root: `grep -rnE 'from install_in_claude import|import install_in_claude$' src bin pyproject.toml` finds no importer other than the entry point `install_in_claude.cli:main`; if it finds one, stop the task as `blocked`, naming it
- [x] Replace the body of `src/install_in_claude/__init__.py` with a one-line module docstring saying the package is the `install-in-claude` command and its modules are `cli`, `links` and `settings`
- [x] In `agents/specs/install-in-claude/spec.md`, change the Module location row for `src/install_in_claude/__init__.py` from "Re-exports the public API below" to say it holds only the package docstring, and that the API below is imported from its own module

**Acceptance Criteria:**

- [x] `src/install_in_claude/__init__.py` holds no import and no `__all__`
- [x] The console script still runs: `source bin/activate.sh && python -c "import install_in_claude.cli as c; print(c.main(['--help']))"` prints the help text

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_cli.py src/tests/test_links.py src/tests/test_settings.py -q` passes (every test module imports the package)

**Notes:**

- Key files: `src/install_in_claude/__init__.py`, `agents/specs/install-in-claude/spec.md`
- The A17 ledger entry is resolved by the change; the next audit re-judges the candidate

---

## Task 4: Refuse a --target or --settings of the wrong kind up front

**Status:** done
**Priority:** medium
**Complexity:** small
**Source Reference:** review-1 decision D1 option A (Sec2 at `cli.py:70`, `cli.py:71`)

**User Story:** As someone running the installer, I want a `--target` that is a file, or a `--settings` that is a directory, to be refused with a message, so that I see what I got wrong instead of a Python traceback.

**Subtasks:**

- [x] Confirm review-1's Answers section records D1 as A; if it does not, stop the task as `blocked`, naming the missing answer
- [x] In `install()` in `src/install_in_claude/cli.py`, after `target` and `settings_path` are resolved and before `read_settings` runs: if `target` exists and is not a directory, print `ERROR: <target> is not a directory` to stderr and return 2; if `settings_path` exists and is not a regular file, print `ERROR: <settings> is not a file` to stderr and return 2
- [x] Add tests to `src/tests/test_cli.py`: a `--target` that is an existing file exits 2 with that message and creates nothing; a `--settings` that is a directory exits 2 with that message and links nothing
- [x] Update `README.md`'s Exit codes row for `2` to name both cases
- [x] Add both cases to the Error handling table in `agents/specs/install-in-claude/spec.md`, beside the `--source` row (exit 2, message, nothing changed)

**Acceptance Criteria:**

- [x] Both new tests pass, and each asserts the exit code, the message on stderr and that the target holds no new link
- [x] A `--target` that does not exist yet is still created, and a missing `--settings` is still treated as empty (existing tests keep passing)

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_cli.py -q` passes

**Notes:**

- Key files: `src/install_in_claude/cli.py`, `src/tests/test_cli.py`, `README.md`, `agents/specs/install-in-claude/spec.md`
- Follow the existing `--source` check's wording and exit code
- D1 covers these two options only; any other input check is outside the decision

---

## Task 5: Report an unreadable settings.json as a SettingsError

**Status:** done
**Priority:** medium
**Complexity:** small
**Source Reference:** review-1 decision D1 option A (A1 at `settings.py:183`)

**User Story:** As someone running the installer, I want a `settings.json` that cannot be read to be reported with a message and exit 1, so that a bad file stops the install before anything changes, with no traceback.

**Subtasks:**

- [x] Confirm review-1's Answers section records D1 as A; if it does not, stop the task as `blocked`, naming the missing answer
- [x] In `read_settings` in `src/install_in_claude/settings.py`, read the file inside a `try`: an `OSError` raises `SettingsError('<path> cannot be read (<strerror>); not changed') from e`, a `UnicodeDecodeError` raises `SettingsError('<path> is not UTF-8 text; not changed') from e`; the invalid-JSON and not-an-object messages stay as they are
- [x] Update the `Raises:` section of `read_settings` to name the new cases
- [x] Add tests to `src/tests/test_settings.py`: a path that is a directory raises `SettingsError` naming the path; a file of invalid UTF-8 bytes raises `SettingsError` naming the path
- [x] Update `README.md`'s Exit codes row for `1` to include a `settings.json` that cannot be read
- [x] Add the case to the Error handling table in `agents/specs/install-in-claude/spec.md` (exit 1, message naming the file, nothing changed), and keep the `OSError` row's scope to linking and writing

**Acceptance Criteria:**

- [x] Both new tests pass
- [x] `read_settings` on a missing file still returns `{}`, and the invalid-JSON test still sees the `json.tool` hint

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `source bin/activate.sh && pytest src/tests/test_settings.py src/tests/test_cli.py -q` passes

**Notes:**

- Depends on Task 1 (the accept marker in `parse_edit` sits in the same file)
- Key files: `src/install_in_claude/settings.py`, `src/tests/test_settings.py`, `README.md`, `agents/specs/install-in-claude/spec.md`
- Avoid a test that relies on `chmod 000`: it passes when the suite runs as root

---

## Task 6: Dismiss the A1 sites the spec keeps propagating

**Status:** done
**Priority:** low
**Complexity:** small
**Source Reference:** review-1 decision D1 option A (A1 sites in `links.py` and `write_settings`)

**Technical Goal:** Record in the A1 ledger that an `OSError` while linking
or writing propagates by design, so the next audit does not report these
sites again.

**Subtasks:**

- [x] Confirm review-1's Answers section records D1 as A; if it does not, stop the task as `blocked`, naming the missing answer
- [x] For each id below, run `python3 ~/.claude/skills/auditme/checks/phaseb.py dismiss . --question A1 '<id>' --reason 'review-1 D1: spec - an OSError while linking or writing propagates'`:
  - `src/install_in_claude/links.py::link_entries::call:dest.mkdir#1`
  - `src/install_in_claude/links.py::link_entries::call:target.mkdir#1`
  - `src/install_in_claude/links.py::link_one::call:dst.symlink_to#1`
  - `src/install_in_claude/links.py::link_one::call:dst.unlink#1`
  - `src/install_in_claude/settings.py::write_settings::call:path.parent.mkdir#1`
  - `src/install_in_claude/settings.py::write_settings::call:pathlib.Path(tmp).unlink#1`
- [x] If `dismiss` refuses an id, stop the task as `blocked`, naming it and the refusal

**Acceptance Criteria:**

- [x] `python3 ~/.claude/skills/auditme/checks/phaseb.py report . --question A1` lists none of the six ids as open
- [x] `agents/audit-reviews/ledger/A1.jsonl` is the only file changed

**Definition of Done:**

- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Depends on Task 5 (it edits `settings.py`; dismiss after the file settles)
- The `read_settings` site is not dismissed: Task 5 fixes it

---

## Task 7: Verify the whole tree and close the review's findings

**Status:** todo
**Priority:** medium
**Complexity:** small
**Source Reference:** review-1, every finding

**Technical Goal:** Check every change together and record the findings as
resolved in the audit summary.

**Subtasks:**

- [ ] Run `python3 ~/.claude/skills/auditme/checks/audit.py . > /tmp/audit-install-in-claude.jsonl` and confirm it holds no `"accepted": false` line
- [ ] Probe both reproduced cases: `--settings` naming a directory and `--target` naming a file each print an `ERROR:` line and exit 2, with no traceback
- [ ] In `agents/audit-reviews/summary.md`, move each finding of review-1 from Unresolved to Recently resolved (resolved in "tasks-1"), and update the hit count line from the run above

**Acceptance Criteria:**

- [ ] The sweep reports zero unaccepted hits
- [ ] `agents/audit-reviews/summary.md` lists no unresolved review-1 finding

**Definition of Done:**

- [ ] `pre-commit run --all-files` exits 0
- [ ] `source bin/activate.sh && pytest src/tests/test_cli.py src/tests/test_links.py src/tests/test_settings.py -q` passes (every module that imports a changed module)
- [ ] `python3 ~/.claude/skills/auditme/checks/audit.py .` prints no unaccepted hit

**Notes:**

- Depends on Tasks 1-6
- Key file: `agents/audit-reviews/summary.md`

---
