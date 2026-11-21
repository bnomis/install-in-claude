"""Edits to Claude Code's settings.json: parsing, merging, reading and writing."""

import dataclasses
import json
import re

# PATH, an optional [MATCH], then = and the JSON value. A PATH part holds no
# '.', '[', ']' or '='; MATCH holds no ']'.
EDIT_RE = re.compile(r'^([^.\[\]=]+(?:\.[^.\[\]=]+)*)(?:\[([^\]]*)\])?=(.*)$', re.DOTALL)


class InstallError(Exception):
    """A failure main() reports as a message and an exit code."""


class EditError(InstallError):
    """A --set-if-absent or --append argument that does not parse; nothing was changed."""


class SettingsError(InstallError):
    """settings.json cannot be merged into; nothing was changed."""


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


def parse_edit(option: str, text: str) -> tuple[tuple[str, ...], str | None, object]:
    """Split `PATH[MATCH]=JSON` into its path, match and parsed value.

    Raises:
        EditError: the text does not have that shape, or the value is not JSON.
    """
    found = EDIT_RE.match(text)
    if found is None:
        raise EditError(f'{option} {text!r}: expected PATH=JSON, PATH a dot-separated key path')
    path_text, match, value_text = found.groups()
    if match == '':
        raise EditError(f'{option} {text!r}: [] holds no text to match')
    try:
        value = json.loads(value_text)
    except ValueError as e:
        raise EditError(f'{option} {text!r}: the value is not valid JSON ({e})') from e
    return tuple(path_text.split('.')), match, value


def parse_set_if_absent(text: str) -> SetIfAbsent:
    """Parse `PATH=JSON`.

    Raises:
        EditError: the text does not parse, or carries a [MATCH].
    """
    path, match, value = parse_edit('--set-if-absent', text)
    if match is not None:
        raise EditError(f'--set-if-absent {text!r}: [MATCH] applies only to --append')
    return SetIfAbsent(path, value)


def parse_append(text: str) -> Append:
    """Parse `PATH=JSON` or `PATH[MATCH]=JSON`.

    Raises:
        EditError: the text does not parse.
    """
    path, match, value = parse_edit('--append', text)
    return Append(path, value, match)
