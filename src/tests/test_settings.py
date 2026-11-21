import pathlib

import pytest

import install_in_claude.settings


def test_set_if_absent_parses_one_part() -> None:
    edit = install_in_claude.settings.parse_set_if_absent('statusLine={"type":"command"}')
    assert edit == install_in_claude.settings.SetIfAbsent(('statusLine',), {'type': 'command'})


def test_set_if_absent_parses_a_dotted_path() -> None:
    edit = install_in_claude.settings.parse_set_if_absent('a.b.c=1')
    assert edit == install_in_claude.settings.SetIfAbsent(('a', 'b', 'c'), 1)


def test_append_parses_a_match() -> None:
    edit = install_in_claude.settings.parse_append('hooks.Stop[auditme-stop.sh]={"a":1}')
    # auditme: accept[literal-duplication] expected value written out in an assertion
    assert edit == install_in_claude.settings.Append(('hooks', 'Stop'), {'a': 1}, 'auditme-stop.sh')


def test_append_without_a_match() -> None:
    edit = install_in_claude.settings.parse_append('hooks.Stop={"a":1}')
    # auditme: accept[literal-duplication] expected value written out in an assertion
    assert edit == install_in_claude.settings.Append(('hooks', 'Stop'), {'a': 1}, None)


def test_the_value_may_hold_equals_and_brackets() -> None:
    edit = install_in_claude.settings.parse_append('k[m]={"cmd":"x=1 [y]"}')
    assert edit == install_in_claude.settings.Append(('k',), {'cmd': 'x=1 [y]'}, 'm')


@pytest.mark.parametrize(
    'text',
    [
        'statusLine',
        '={"a":1}',
        'a..b=1',
        '.a=1',
        'a.=1',
        'a=not json',
        'a=',
        'a[]=1',
    ],
)
def test_malformed_append_is_refused(text: str) -> None:
    with pytest.raises(install_in_claude.settings.EditError, match='--append'):
        install_in_claude.settings.parse_append(text)


@pytest.mark.parametrize('text', ['statusLine', 'a=not json', 'a[m]=1'])
def test_malformed_set_if_absent_is_refused(text: str) -> None:
    with pytest.raises(install_in_claude.settings.EditError, match='--set-if-absent'):
        install_in_claude.settings.parse_set_if_absent(text)


def test_an_edit_error_is_an_install_error() -> None:
    assert issubclass(install_in_claude.settings.EditError, install_in_claude.settings.InstallError)
    assert issubclass(install_in_claude.settings.SettingsError, install_in_claude.settings.InstallError)


def apply(settings: dict[str, object], *edits: object) -> tuple[dict[str, object], list[install_in_claude.settings.EditOutcome]]:
    return install_in_claude.settings.apply_edits(settings, list(edits))  # type: ignore[arg-type]


STATUS = install_in_claude.settings.parse_set_if_absent('statusLine={"type":"command","command":"x"}')
STOP = install_in_claude.settings.parse_append('hooks.Stop[stop.sh]={"hooks":[{"type":"command","command":"bash stop.sh"}]}')


def test_set_when_absent() -> None:
    result, outcomes = apply({}, STATUS)
    assert result == {'statusLine': {'type': 'command', 'command': 'x'}}
    assert outcomes == [install_in_claude.settings.EditOutcome('statusLine', 'set', True)]


def test_kept_when_present_whatever_the_value() -> None:
    result, outcomes = apply({'statusLine': None}, STATUS)
    assert result == {'statusLine': None}
    assert outcomes == [install_in_claude.settings.EditOutcome('statusLine', 'set', False)]


def test_set_creates_missing_objects() -> None:
    result, _ = apply({}, install_in_claude.settings.parse_set_if_absent('a.b=1'))
    assert result == {'a': {'b': 1}}


def test_append_creates_a_missing_list() -> None:
    result, outcomes = apply({}, STOP)
    assert result == {'hooks': {'Stop': [STOP.value]}}
    assert outcomes == [install_in_claude.settings.EditOutcome('hooks.Stop', 'append', True)]


def test_append_keeps_other_entries_and_keys() -> None:
    other = {'hooks': [{'type': 'command', 'command': 'other-stop'}]}
    original = {'model': 'x', 'hooks': {'Stop': [other], 'PreToolUse': [{'matcher': 'Bash', 'hooks': []}]}}
    result, _ = apply(original, STOP)
    assert result == {'model': 'x', 'hooks': {'Stop': [other, STOP.value], 'PreToolUse': [{'matcher': 'Bash', 'hooks': []}]}}


def test_append_skips_on_a_match() -> None:
    existing = {'hooks': {'Stop': [{'hooks': [{'command': 'bash /elsewhere/stop.sh'}]}]}}
    result, outcomes = apply(existing, STOP)
    assert result == existing
    assert outcomes == [install_in_claude.settings.EditOutcome('hooks.Stop', 'append', False)]


def test_append_without_match_skips_only_an_equal_element() -> None:
    edit = install_in_claude.settings.parse_append('xs={"a":1}')
    assert apply({'xs': [{'a': 1}]}, edit)[0] == {'xs': [{'a': 1}]}
    assert apply({'xs': [{'a': 1, 'b': 2}]}, edit)[0] == {'xs': [{'a': 1, 'b': 2}, {'a': 1}]}


def test_append_is_not_skipped_when_the_match_is_absent() -> None:
    existing = {'hooks': {'Stop': [{'hooks': [{'command': 'bash other.sh'}]}]}}
    result, _ = apply(existing, STOP)
    assert result['hooks']['Stop'][-1] == STOP.value  # type: ignore[index]


@pytest.mark.parametrize(
    ('settings', 'edit', 'found'),
    [
        ({'hooks': 1}, STOP, 'int'),
        ({'hooks': {'Stop': {}}}, STOP, 'dict'),
        ({'a': 'x'}, install_in_claude.settings.parse_set_if_absent('a.b=1'), 'str'),
    ],
)
def test_wrong_types_are_refused(settings: dict[str, object], edit: object, found: str) -> None:
    with pytest.raises(install_in_claude.settings.SettingsError, match=found):
        apply(settings, edit)


def test_edits_apply_in_order() -> None:
    first = install_in_claude.settings.parse_append('xs=1')
    second = install_in_claude.settings.parse_append('xs=2')
    again = install_in_claude.settings.parse_append('xs=1')
    result, outcomes = apply({}, first, second, again)
    assert result == {'xs': [1, 2]}
    assert [outcome.changed for outcome in outcomes] == [True, True, False]


def test_the_input_is_not_mutated() -> None:
    original = {'hooks': {'Stop': []}}
    apply(original, STOP, STATUS)
    assert original == {'hooks': {'Stop': []}}


@pytest.mark.parametrize(
    ('outcome', 'dry_run', 'text'),
    [
        (install_in_claude.settings.EditOutcome('statusLine', 'set', True), False, 'Set statusLine in f.json'),
        (install_in_claude.settings.EditOutcome('statusLine', 'set', True), True, 'Would set statusLine in f.json'),
        (install_in_claude.settings.EditOutcome('statusLine', 'set', False), False, 'statusLine already set in f.json'),
        (install_in_claude.settings.EditOutcome('hooks.Stop', 'append', True), False, 'Appended to hooks.Stop in f.json'),
        (install_in_claude.settings.EditOutcome('hooks.Stop', 'append', True), True, 'Would append to hooks.Stop in f.json'),
        (install_in_claude.settings.EditOutcome('hooks.Stop', 'append', False), True, 'hooks.Stop already has a matching entry in f.json'),
    ],
)
def test_outcome_messages(outcome: install_in_claude.settings.EditOutcome, dry_run: bool, text: str) -> None:
    assert outcome.message(pathlib.Path('f.json'), dry_run) == text


def test_an_absent_file_reads_as_empty(tmp_path: pathlib.Path) -> None:
    assert install_in_claude.settings.read_settings(tmp_path / 'settings.json') == {}


@pytest.mark.parametrize(('content', 'reason'), [('{not json', 'not valid JSON'), ('[1, 2]', 'not a JSON object')])
def test_invalid_settings_are_refused(tmp_path: pathlib.Path, content: str, reason: str) -> None:
    path = tmp_path / 'settings.json'
    path.write_text(content)
    with pytest.raises(install_in_claude.settings.SettingsError, match=reason):
        install_in_claude.settings.read_settings(path)
    assert path.read_text() == content
    assert not path.with_name('settings.json.orig').exists()


def test_a_directory_is_reported_as_unreadable(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'settings.json'
    path.mkdir()
    with pytest.raises(install_in_claude.settings.SettingsError, match=f'{path} cannot be read'):
        install_in_claude.settings.read_settings(path)


def test_a_non_utf8_file_is_refused(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'settings.json'
    path.write_bytes(b'\xff\xfe\x00{')
    with pytest.raises(install_in_claude.settings.SettingsError, match=f'{path} is not UTF-8 text'):
        install_in_claude.settings.read_settings(path)
    assert not path.with_name('settings.json.orig').exists()


def test_a_written_file_round_trips(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'new' / 'settings.json'
    install_in_claude.settings.write_settings(path, {'a': [1, {'b': 'c'}]})
    assert install_in_claude.settings.read_settings(path) == {'a': [1, {'b': 'c'}]}
    assert path.read_text().endswith('}\n')


def test_the_mode_is_kept(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'settings.json'
    path.write_text('{}')
    path.chmod(0o600)
    install_in_claude.settings.write_settings(path, {'a': 1})
    assert path.stat().st_mode & 0o777 == 0o600


def test_the_original_is_kept_once(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'settings.json'
    path.write_text('{"model": "x"}')
    install_in_claude.settings.write_settings(path, {'a': 1})
    install_in_claude.settings.write_settings(path, {'a': 2})
    assert path.with_name('settings.json.orig').read_text() == '{"model": "x"}'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['settings.json', 'settings.json.orig']


def test_a_new_file_gets_no_original(tmp_path: pathlib.Path) -> None:
    path = tmp_path / 'settings.json'
    install_in_claude.settings.write_settings(path, {})
    # auditme: accept[literal-duplication] expected value written out in an assertion
    assert sorted(p.name for p in tmp_path.iterdir()) == ['settings.json']
