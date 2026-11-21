# install-in-claude

**Version:** 1.0
**Status:** proposed
**Date:** 2026-11-21
**Review page:** https://claude.ai/artifact/M8d28UtW21aRK13RdXMX8N

`install-in-claude` links a project's Claude Code files into `~/.claude/` and
merges the `settings.json` entries the project needs. Before this repository,
the same script was copied as `bin/install-claude.py` into several projects (as
of 2026-11-21), and each copy differed only in what it hard-coded: the source
directory (the project's own `claude/`), and the `settings.json` entry it
registered (a status line, a Stop hook, or none). Every fix had to be made once
per copy, and the copies had already drifted (one caught every exception and
exited with its message; the others let an unexpected one propagate). This tool
takes everything project-specific as command-line arguments, so one version
serves every project, and each project pins the commit it was tested with.

## Module location

`src/install_in_claude/`, a package with the console script
`install-in-claude` (`[project.scripts]` in `pyproject.toml`). The name is
`install-in-claude` wherever a hyphen is allowed - the repository, the
distribution (`name = "install-in-claude"`) and the command - and
`install_in_claude` only for the import package, since a Python module name
cannot hold a hyphen:

| File | Holds |
|---|---|
| `src/install_in_claude/__init__.py` | Re-exports the public API below |
| `src/install_in_claude/cli.py` | The `cappa` command and `main()` |
| `src/install_in_claude/links.py` | Linking and the dangling-link report |
| `src/install_in_claude/settings.py` | Edit parsing, merging, reading and writing `settings.json` |
| `src/tests/test_cli.py`, `test_links.py`, `test_settings.py` | Tests, mirroring the modules |

## API

```python
# cli.py
@cappa.command(name='install-in-claude')
@dataclasses.dataclass
class InstallInClaude:
    """Link a project's Claude Code files into ~/.claude and merge its settings."""

    source: typing.Annotated[pathlib.Path, cappa.Arg(long=True)]
    target: typing.Annotated[pathlib.Path | None, cappa.Arg(long=True)] = None
    settings: typing.Annotated[pathlib.Path | None, cappa.Arg(long=True)] = None
    set_if_absent: typing.Annotated[list[str], cappa.Arg(long='--set-if-absent')] = dataclasses.field(default_factory=list)
    append: typing.Annotated[list[str], cappa.Arg(long=True)] = dataclasses.field(default_factory=list)
    dry_run: typing.Annotated[bool, cappa.Arg(long=True)] = False


def main(argv: collections.abc.Sequence[str] | None = None) -> int:
    """Parse argv, validate every edit, link, then write settings. Returns the exit code."""


# settings.py
@dataclasses.dataclass(frozen=True)
class SetIfAbsent:
    """Set the value at `path` only when the key is missing."""

    path: tuple[str, ...]
    value: object


@dataclasses.dataclass(frozen=True)
class Append:
    """Append `value` to the list at `path` unless it is already there.

    Already there means: an element contains `match` in its JSON text when
    `match` is set, else an element equal to `value`.
    """

    path: tuple[str, ...]
    value: object
    match: str | None


def parse_set_if_absent(text: str) -> SetIfAbsent:
    """Parse `PATH=JSON`. Raises EditError."""


def parse_append(text: str) -> Append:
    """Parse `PATH=JSON` or `PATH[MATCH]=JSON`. Raises EditError."""


@dataclasses.dataclass(frozen=True)
class EditOutcome:
    """What one edit did: its dotted path, its kind ('set' or 'append'), and whether it changed anything."""

    path: str
    kind: str
    changed: bool

    def message(self, settings_path: pathlib.Path, dry_run: bool) -> str:
        """`Set statusLine in <file>`, `Would append to hooks.Stop in <file>`, `statusLine already set in <file>`, ..."""


def apply_edits(settings: dict[str, object], edits: collections.abc.Sequence[SetIfAbsent | Append]) -> tuple[dict[str, object], list[EditOutcome]]:
    """Return a new settings object with the edits applied, and one outcome per edit. Pure; raises SettingsError."""


def read_settings(path: pathlib.Path) -> dict[str, object]:
    """The parsed file, {} when absent. Raises SettingsError."""


def write_settings(path: pathlib.Path, settings: dict[str, object]) -> None:
    """Write atomically, keeping the mode; copy the first original to settings.json.orig."""


# links.py
def link_entries(source: pathlib.Path, target: pathlib.Path, dry_run: bool) -> list[str]:
    """Link each entry of source into target; returns one message per link."""


def dangling_links(target: pathlib.Path, max_depth: int = 2) -> list[pathlib.Path]:
    """Symlinks under target, at most max_depth levels down, whose target is gone."""
```

## Edits to `settings.json`

Both options are repeatable. Every `--set-if-absent` applies first, then
every `--append`, each in the order given.

- `PATH` is a dot-separated key path (`statusLine`, `hooks.Stop`); each part is
  non-empty and holds no `.`, `[`, `]` or `=`. Missing objects on the way are
  created.
- `JSON` is everything after the first `=` following `PATH` (or `[MATCH]`),
  parsed with `json.loads`.
- `--set-if-absent PATH=JSON` sets the key only when it is missing; a key
  already present, whatever its value, is left alone.
- `--append PATH=JSON` appends to the list at `PATH`, creating it when
  missing, unless an element equal to `JSON` is already in it.
- `--append PATH[MATCH]=JSON` skips instead when any element's compact JSON
  text (`json.dumps(element, sort_keys=True, separators=(',', ':'))`) contains
  `MATCH`, plain text without `]`. So a hook registered with a different
  command line naming the same script is not added twice.
- The file is written only when an edit changed something; an unchanged file
  is not rewritten and gains no `.orig`.

## Error handling

| Failure | Exit | What happens |
|---|---|---|
| Bad arguments, or an edit that does not parse (no `=`, an empty or invalid `PATH`, `[]` with no `MATCH`, invalid JSON): `EditError` | 2 | Message naming the argument; nothing changed. |
| `--source` is not a directory | 2 | `ERROR: <source> is not a directory`; nothing changed. |
| `settings.json` is not valid JSON, or not an object: `SettingsError` | 1 | Message naming the file and `python3 -m json.tool <file>`; nothing changed. |
| An edit meets the wrong type (a `PATH` part is not an object, an `--append` target is not a list): `SettingsError` | 1 | Message naming the path and the type found; nothing changed. |
| An `OSError` while linking or writing | traceback | Propagates. Links already made stay; `settings.json` is unchanged, as it is written last and atomically. |

`EditError` and `SettingsError` are defined in `settings.py`, both subclasses
of `InstallError(Exception)`. `main()` turns them into a message on stderr and
the exit code; nothing else is caught.

## Implementation

`main()` works in an order that keeps a failure from leaving a half-done
install:

1. Parse the arguments with `cappa`, then every `--set-if-absent` and
   `--append` into `SetIfAbsent` and `Append`. Any `EditError` stops here.
2. Resolve `--source` and check it is a directory; `--target` defaults to
   `~/.claude` and `--settings` to `<target>/settings.json`. All three are
   expanded and resolved through symlinks alike, so the relative links
   computed between them hold.
3. Read the settings and apply the edits in memory (`apply_edits`). A
   `SettingsError` stops here, before any link is made.
4. Link: for each top-level entry of `source` not starting with `.`, a file is
   linked as `target/<name>`; a directory is created in `target` and each of
   its entries linked into it, one level only (so `claude/skills/auditme`
   becomes the link `~/.claude/skills/auditme`). A link in the way is
   replaced; a real file in the way is renamed to `<name>.orig`, then
   `<name>.orig.2` and on. Each link is relative
   (`src.parent.relative_to(dst.parent, walk_up=True)`), printed as
   `Linking <src> to <dst> via <relative>`.
5. Report `dangling_links(target)`: each path, then one `rm ...` line to remove
   them all. Nothing is deleted.
6. Write the settings if any edit changed them, then print each edit's
   `EditOutcome.message` (`Set statusLine in <file>`, `statusLine already set in <file>`,
   `Appended to hooks.Stop in <file>`, `hooks.Stop already has a matching
   entry in <file>`).

With `--dry-run`, steps 4 and 6 print `Would link ...` and `Would set ...` /
`Would append ...` and change nothing; the dangling-link report still runs.
Today's copies read the settings after linking, so a bad `settings.json` left
the links made; reading first is the one deliberate change of behaviour.

## Settings

| Option | Type | Default | Description |
|---|---|---|---|
| `--source DIR` | path | required | The project's Claude files, usually its `claude/` |
| `--target DIR` | path | `~/.claude` | Where the links go |
| `--settings FILE` | path | `<target>/settings.json` | The settings file the edits merge into |
| `--set-if-absent PATH=JSON` | repeatable | none | See [Edits](#edits-to-settingsjson) |
| `--append PATH[MATCH]=JSON` | repeatable | none | See [Edits](#edits-to-settingsjson) |
| `--dry-run` | flag | off | Print the plan; change nothing |

`--source` has no default: the tool serves many projects and none of their
layouts is built in.

## Consumers

Restated so the options can be checked against real use. Each project replaces
its `bin/install-claude.py` with a `bin/install-claude.sh` that runs the
pinned commit:

```shell
uvx --from "git+ssh://git@github.com/bnomis/install-in-claude.git@<commit>" \
    install-in-claude --source "$REPO/claude" <its arguments> "$@"
```

| A project that | Its arguments, as options |
|---|---|
| sets a status line when none is set | `--set-if-absent 'statusLine={"command":"~/.claude/statusline.py","type":"command"}'` |
| registers a Stop hook once, by script name | `--append 'hooks.Stop[auditme-stop.sh]={"hooks":[{"type":"command","command":"bash \"$HOME/.claude/hooks/auditme-stop.sh\""}]}'` |
| writes no settings | none |

Each switch is its own spec amendment in that project's repository; the order
is in [rollout.md](rollout.md). Like every file here, this spec names no
project it serves (see [Repository](#repository)).

## Repository

- `pyproject.toml`: `requires-python = ">=3.14"`, the console script, ruff
  configured as the shared rules ask, `pytest` and `ruff` as dev dependencies.
- `bin/activate.sh`: activates `.venv` and puts `src/` on `PYTHONPATH`, as the
  shared Python rules ask, so tests run as `pytest` without `uv run`.
- `README.md`, the user guide: install (`uvx`, or `uv tool install` for one
  machine), the options table, the consumer invocations above as examples,
  and why `--source` has no default.
- `AGENTS.md`: the test command, and that the repository serves many projects
  and names none it was run on in code, tests, fixtures or commits.
- `.pre-commit-config.yaml`: ruff-check and ruff-format at the `rev` that
  matches the ruff in `uv.lock`, and the agents repository's
  `no-project-names` hook (`git@github.com:bnomis/agents.git`, the `rev` the
  other shared repositories pin) with `args: [--allow=install-in-claude]`.
  Installed with `pre-commit install --hook-type pre-commit --hook-type
  pre-push --hook-type commit-msg`.

## Testing

Ported from the copies' suites, plus the new parts, all in a temporary
directory with `--target` and `--settings` pointed into it:

- links: a new file; an existing link replaced; a real file renamed `.orig`,
  then `.orig.2`; directories linked one level down; top-level dotfiles
  skipped; a second run changes nothing.
- dangling report: a dangling link reported with its `rm` line; silence when
  all resolve; nothing below `max_depth`.
- edits: each parse error; set when absent, kept when present; append to a
  missing list, skipped on an equal element, skipped on a `MATCH`, kept beside
  other entries; wrong types refused; edits applied in order.
- settings file: absent file created; other keys and hooks kept; mode kept;
  `.orig` written once; an unchanged file not rewritten; invalid JSON and a
  non-object refused with nothing changed, and no link made.
- CLI: each consumer's invocation end to end; `--dry-run` changes nothing;
  exit codes 0, 1 and 2.

## External dependencies

- Python 3.14 or later.
- `cappa` 0.33.0, released 2026-10-09, outside a 14-day `exclude-newer`
  window; `pyproject.toml` asks `cappa>=0.33.0` and `uv.lock` pins it.
- `uv`, for `uvx` in each consumer's wrapper; SSH access to the private
  `bnomis/install-in-claude` on GitHub for the first run of each pinned
  commit, cached after.
