"""The install-in-claude command."""

import collections.abc
import dataclasses
import pathlib
import shlex
import sys
import typing

import cappa

import install_in_claude.links
import install_in_claude.settings


@cappa.command(name='install-in-claude')
@dataclasses.dataclass
class InstallInClaude:
    """Link a project's Claude Code files into ~/.claude and merge its settings."""

    source: typing.Annotated[pathlib.Path, cappa.Arg(long=True, help="The project's Claude files, usually its claude/ directory.")]
    target: typing.Annotated[pathlib.Path | None, cappa.Arg(long=True, help='Where the links go. Default: ~/.claude.')] = None
    settings: typing.Annotated[pathlib.Path | None, cappa.Arg(long=True, help='The settings file to merge into. Default: TARGET/settings.json.')] = None
    set_if_absent: typing.Annotated[
        list[str],
        cappa.Arg(
            long='--set-if-absent', action=cappa.ArgAction.append, value_name='PATH=JSON', help='Set a settings key only when it is missing. Repeatable.'
        ),
    ] = dataclasses.field(default_factory=list)
    append: typing.Annotated[
        list[str],
        cappa.Arg(
            long=True,
            action=cappa.ArgAction.append,
            value_name='PATH[MATCH]=JSON',
            help='Append to a settings list unless an equal entry, or one containing MATCH, is there. Repeatable.',
        ),
    ] = dataclasses.field(default_factory=list)
    dry_run: typing.Annotated[bool, cappa.Arg(long=True, help='Print what would change; change nothing.')] = False


def edits_from(command: InstallInClaude) -> list[install_in_claude.settings.SetIfAbsent | install_in_claude.settings.Append]:
    """Every edit, set-if-absent ones first, each group in the order given.

    Raises:
        EditError: an argument does not parse.
    """
    edits: list[install_in_claude.settings.SetIfAbsent | install_in_claude.settings.Append] = [
        install_in_claude.settings.parse_set_if_absent(text) for text in command.set_if_absent
    ]
    edits.extend(install_in_claude.settings.parse_append(text) for text in command.append)
    return edits


def install(command: InstallInClaude) -> int:
    """Run an install, in an order that leaves nothing half done on a refused input.

    Raises:
        EditError: an edit does not parse (before anything is changed).
        SettingsError: the settings cannot be merged into (before anything is changed).
    """
    edits = edits_from(command)
    source = command.source.expanduser().resolve()
    if not source.is_dir():
        print(f'ERROR: {source} is not a directory', file=sys.stderr)
        return 2
    # Resolve every path the same way: a relative link computed between a
    # resolved source and an unresolved target (a /var that is a link to
    # /private/var) points nowhere.
    target = (command.target or pathlib.Path('~/.claude')).expanduser().resolve()
    settings_path = (command.settings or target / 'settings.json').expanduser().resolve()

    current = install_in_claude.settings.read_settings(settings_path)
    updated, outcomes = install_in_claude.settings.apply_edits(current, edits)

    for message in install_in_claude.links.link_entries(source, target, command.dry_run):
        print(message)

    dangling = install_in_claude.links.dangling_links(target)
    if dangling:
        print('Dangling symlinks found:')
        for path in dangling:
            print(f'  {path}')
        print('Remove with:')
        # Quoted, so a name holding a space or a shell character is removed
        # as itself when the line is pasted into a shell.
        print(f'rm -- {" ".join(shlex.quote(str(path)) for path in dangling)}')

    if updated != current and not command.dry_run:
        install_in_claude.settings.write_settings(settings_path, updated)
    for outcome in outcomes:
        print(outcome.message(settings_path, command.dry_run))
    return 0


def main(argv: collections.abc.Sequence[str] | None = None) -> int:
    """Parse argv, validate every edit, link, then write settings. Returns the exit code."""
    command = cappa.parse(InstallInClaude, argv=list(sys.argv[1:] if argv is None else argv))
    try:
        return install(command)
    except install_in_claude.settings.EditError as e:
        # auditme: accept[except-interpolation] the domain error's message is the report the user sees
        print(f'ERROR: {e}', file=sys.stderr)
        return 2
    except install_in_claude.settings.SettingsError as e:
        # auditme: accept[except-interpolation] the domain error's message is the report the user sees
        print(f'ERROR: {e}', file=sys.stderr)
        return 1
