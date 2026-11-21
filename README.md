# install-in-claude

Links a project's Claude Code files (skills, rules, hooks, `CLAUDE.md`) into
`~/.claude/`, and merges the `settings.json` entries the project needs. One
version serves every project: everything project-specific is given on the
command line, so no project keeps its own copy of an installer.

## Run it

You need [uv](https://docs.astral.sh/uv/) and SSH access to
`bnomis/install-in-claude` on GitHub. Pin the commit your project was tested
with:

```shell
uvx --from "git+ssh://git@github.com/bnomis/install-in-claude.git@<commit>" \
    install-in-claude --source claude --dry-run
```

`<commit>` is a commit of this repository, for the newest:
`git ls-remote git@github.com:bnomis/install-in-claude.git refs/heads/main`,
first field. `uvx` caches it after the first run. Drop `--dry-run` to install.

To have the command on your `PATH` on one machine instead:

```shell
uv tool install "git+ssh://git@github.com/bnomis/install-in-claude.git@<commit>"
install-in-claude --source claude
```

In a project, put the call in `bin/install-claude.sh` so everyone runs the
same commit with the same options:

```shell
#!/usr/bin/env bash
set -euo pipefail
REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec uvx --from "git+ssh://git@github.com/bnomis/install-in-claude.git@<commit>" \
    install-in-claude --source "$REPO/claude" "$@"
```

## What it does

1. Checks every option first. A malformed edit, a missing `--source` or an
   unreadable `settings.json` stops it before anything changes.
2. Links each top-level entry of `--source` (skipping names starting with
   `.`) into `--target`. A file becomes `TARGET/<name>`; a directory is
   created in the target and each of its entries linked into it, one level
   down, so `claude/skills/probe/` becomes the link
   `~/.claude/skills/probe`. Links are relative.
3. In the way of a link: an old link is replaced; a real file is renamed to
   `<name>.orig` (then `<name>.orig.2`, ...), never deleted.
4. Reports dangling links in the target (two levels deep), with one `rm`
   command, each path quoted, to remove them. It never deletes them itself: a dangling link may
   belong to another project.
5. Applies the settings edits, writes `settings.json` only if something
   changed, atomically and keeping its mode, and keeps the first original as
   `settings.json.orig`.

Running it again changes nothing.

## Options

| Option | Default | What it does |
|---|---|---|
| `--source DIR` | required | The project's Claude files, usually its `claude/` |
| `--target DIR` | `~/.claude` | Where the links go |
| `--settings FILE` | `TARGET/settings.json` | The settings file the edits merge into |
| `--set-if-absent PATH=JSON` | none | Set a key only when it is missing. Repeatable |
| `--append PATH=JSON` | none | Append to a list unless an equal entry is there. Repeatable |
| `--append PATH[MATCH]=JSON` | none | Append unless an entry's JSON text contains `MATCH` |
| `--dry-run` | off | Print what would change; change nothing |

`--source` has no default because the tool serves many projects and builds in
none of their layouts.

### Settings edits

`PATH` is a dot-separated key path (`statusLine`, `hooks.Stop`); missing
objects on the way are created. `JSON` is everything after the `=`. Every
`--set-if-absent` applies first, then every `--append`, each in the order
given.

`--set-if-absent` leaves a key that is already present alone, whatever its
value, so a setting you chose by hand is never overwritten.

`--append PATH[MATCH]=JSON` exists for hooks. An entry counts as already
there when its compact JSON text (sorted keys, no spaces) contains `MATCH`,
so a hook you registered by hand with a different command line, but naming
the same script, is not added twice. `MATCH` is plain text and cannot hold
`]`.

### Examples

A project that sets a status line when none is set:

```shell
install-in-claude --source claude \
    --set-if-absent 'statusLine={"command":"~/.claude/statusline.py","type":"command"}'
```

A project that registers a Stop hook once, by script name:

```shell
install-in-claude --source claude \
    --append 'hooks.Stop[auditme-stop.sh]={"hooks":[{"type":"command","command":"bash \"$HOME/.claude/hooks/auditme-stop.sh\""}]}'
```

A project with no settings to write:

```shell
install-in-claude --source claude
```

## Exit codes

| Exit | Meaning |
|---|---|
| `0` | Installed, or nothing to do |
| `1` | `settings.json` is not valid JSON or not an object, or an edit meets the wrong type (a key on the path is not an object, an `--append` target is not a list); nothing changed |
| `2` | Bad arguments, an edit that does not parse, or `--source` is not a directory; nothing changed |

## Develop

```shell
uv sync
pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
source bin/activate.sh && pytest src/tests -q
```

The design is [agents/specs/install-in-claude/spec.md](agents/specs/install-in-claude/spec.md).
