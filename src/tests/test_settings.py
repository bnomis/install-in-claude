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
    assert edit == install_in_claude.settings.Append(('hooks', 'Stop'), {'a': 1}, 'auditme-stop.sh')


def test_append_without_a_match() -> None:
    edit = install_in_claude.settings.parse_append('hooks.Stop={"a":1}')
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
