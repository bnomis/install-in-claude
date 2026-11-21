"""Edits to Claude Code's settings.json: parsing, merging, reading and writing."""

import collections.abc
import copy
import dataclasses
import json
import os
import pathlib
import re
import shutil
import tempfile

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
        # auditme: accept[except-interpolation] main() prints str(e), so the parser's position reaches the user only here
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


# How EditOutcome.message words an edit, by (kind, dry_run) when it changed
# something and by kind when it did not.
ACTIONS = {
    ('append', False): 'Appended to',
    ('append', True): 'Would append to',
    ('set', False): 'Set',
    ('set', True): 'Would set',
}
UNCHANGED = {
    'append': 'already has a matching entry',
    'set': 'already set',
}


@dataclasses.dataclass(frozen=True)
class EditOutcome:
    """What one edit did: its dotted path, its kind ('set' or 'append'), and whether it changed anything."""

    path: str
    kind: str
    changed: bool

    def message(self, settings_path: pathlib.Path, dry_run: bool) -> str:
        """The line printed for this edit."""
        if not self.changed:
            return f'{self.path} {UNCHANGED[self.kind]} in {settings_path}'
        action = ACTIONS[(self.kind, dry_run)]
        return f'{action} {self.path} in {settings_path}'


def compact(value: object) -> str:
    """The JSON text a [MATCH] is looked for in."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def parent_object(settings: dict[str, object], path: tuple[str, ...]) -> dict[str, object]:
    """The object holding path's last key, creating missing objects on the way.

    Raises:
        SettingsError: a part on the way is not an object.
    """
    node = settings
    for depth, key in enumerate(path[:-1]):
        child = node.setdefault(key, {})
        if not isinstance(child, dict):
            raise SettingsError(f'{".".join(path[: depth + 1])} is {type(child).__name__}, not an object; cannot apply an edit to {".".join(path)}')
        node = child
    return node


def apply_edits(settings: dict[str, object], edits: collections.abc.Sequence[SetIfAbsent | Append]) -> tuple[dict[str, object], list[EditOutcome]]:
    """Return a new settings object with the edits applied, and one outcome per edit.

    Pure: `settings` is not changed.

    Raises:
        SettingsError: an edit meets a value of the wrong type.
    """
    result = copy.deepcopy(settings)
    outcomes = []
    for edit in edits:
        dotted = '.'.join(edit.path)
        parent = parent_object(result, edit.path)
        key = edit.path[-1]
        if isinstance(edit, SetIfAbsent):
            changed = key not in parent
            if changed:
                parent[key] = copy.deepcopy(edit.value)
            outcomes.append(EditOutcome(dotted, 'set', changed))
            continue
        items = parent.setdefault(key, [])
        if not isinstance(items, list):
            raise SettingsError(f'{dotted} is {type(items).__name__}, not a list; cannot append to it')
        if edit.match is None:
            present = edit.value in items
        else:
            present = any(edit.match in compact(item) for item in items)
        if not present:
            items.append(copy.deepcopy(edit.value))
        outcomes.append(EditOutcome(dotted, 'append', not present))
    return result, outcomes


def read_settings(path: pathlib.Path) -> dict[str, object]:
    """The parsed settings file, {} when it is absent.

    Raises:
        SettingsError: the file cannot be read, is not UTF-8 text, is not
            valid JSON, or is not a JSON object.
    """
    if not path.exists():
        return {}
    try:
        text = path.read_text()
    except UnicodeDecodeError as e:
        raise SettingsError(f'{path} is not UTF-8 text; not changed') from e
    except OSError as e:
        raise SettingsError(f'{path} cannot be read ({e.strerror}); not changed') from e
    try:
        settings = json.loads(text)
    except ValueError as e:
        raise SettingsError(f'{path} is not valid JSON; not changed (check it with: python3 -m json.tool {path})') from e
    if not isinstance(settings, dict):
        raise SettingsError(f'{path} is not a JSON object; not changed')
    return settings


def write_settings(path: pathlib.Path, settings: dict[str, object]) -> None:
    """Write the settings atomically, keeping the file's mode.

    The first time an existing file is changed, its original is kept as
    settings.json.orig; a later write leaves that copy alone.
    """
    if path.exists():
        orig = path.with_name(path.name + '.orig')
        if not orig.exists():
            shutil.copy2(path, orig)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f'{path.name}.')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(json.dumps(settings, indent=2) + '\n')
        if path.exists():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        pathlib.Path(tmp).unlink(missing_ok=True)
        raise
