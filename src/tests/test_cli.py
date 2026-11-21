import json
import pathlib

import pytest

import install_in_claude.cli

STATUS_LINE = 'statusLine={"command":"~/.claude/statusline.py","type":"command"}'
STOP_HOOK = 'hooks.Stop[auditme-stop.sh]={"hooks":[{"type":"command","command":"bash \\"$HOME/.claude/hooks/auditme-stop.sh\\""}]}'


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    source = tmp_path / 'repo' / 'claude'
    (source / 'skills' / 'probe').mkdir(parents=True)
    (source / 'skills' / 'probe' / 'SKILL.md').write_text('probe\n')
    (source / 'CLAUDE.md').write_text('top\n')
    return source


def run(source: pathlib.Path, target: pathlib.Path, *extra: str) -> int:
    return install_in_claude.cli.main(['--source', str(source), '--target', str(target), *extra])


def snapshot(target: pathlib.Path) -> dict[str, str]:
    return {
        str(p.relative_to(target)): p.readlink().as_posix() if p.is_symlink() else p.read_text()
        for p in sorted(target.rglob('*'))
        if p.is_symlink() or p.is_file()
    }


@pytest.mark.parametrize(
    ('extra', 'expected'),
    [
        ([], None),
        (['--set-if-absent', STATUS_LINE], {'statusLine': {'command': '~/.claude/statusline.py', 'type': 'command'}}),
        (
            ['--append', STOP_HOOK],
            {'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'bash "$HOME/.claude/hooks/auditme-stop.sh"'}]}]}},
        ),
    ],
    ids=['no-settings', 'status-line', 'stop-hook'],
)
def test_each_consumer_invocation_twice(project: pathlib.Path, tmp_path: pathlib.Path, extra: list[str], expected: dict[str, object] | None) -> None:
    target = tmp_path / 'home' / '.claude'
    assert run(project, target, *extra) == 0
    first = snapshot(target)
    assert (target / 'skills' / 'probe' / 'SKILL.md').read_text() == 'probe\n'
    settings = target / 'settings.json'
    if expected is None:
        assert not settings.exists()
    else:
        assert json.loads(settings.read_text()) == expected
    assert run(project, target, *extra) == 0
    assert snapshot(target) == first


def test_a_stop_hook_naming_the_script_elsewhere_is_not_added(project: pathlib.Path, tmp_path: pathlib.Path) -> None:
    target = tmp_path / 'home' / '.claude'
    target.mkdir(parents=True)
    original = json.dumps({'hooks': {'Stop': [{'hooks': [{'command': 'bash /elsewhere/auditme-stop.sh'}]}]}})
    (target / 'settings.json').write_text(original)
    assert run(project, target, '--append', STOP_HOOK) == 0
    assert (target / 'settings.json').read_text() == original
    assert not (target / 'settings.json.orig').exists()


def test_a_dry_run_changes_nothing(project: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / 'home' / '.claude'
    assert run(project, target, '--set-if-absent', STATUS_LINE, '--dry-run') == 0
    assert not target.exists()
    out = capsys.readouterr().out
    assert 'Would link ' in out
    assert 'Would set statusLine in ' in out


def test_an_invalid_edit_exits_2_with_nothing_linked(project: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / 'home' / '.claude'
    assert run(project, target, '--append', 'not-an-edit') == 2
    assert not target.exists()
    assert '--append' in capsys.readouterr().err


def test_a_missing_source_exits_2(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / 'home' / '.claude'
    assert run(tmp_path / 'absent', target) == 2
    assert not target.exists()
    assert 'is not a directory' in capsys.readouterr().err


def test_invalid_settings_exit_1_with_nothing_linked(project: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / 'home' / '.claude'
    target.mkdir(parents=True)
    (target / 'settings.json').write_text('{not json')
    assert run(project, target, '--set-if-absent', STATUS_LINE) == 1
    assert (target / 'settings.json').read_text() == '{not json'
    assert sorted(p.name for p in target.iterdir()) == ['settings.json']
    assert 'not valid JSON' in capsys.readouterr().err


def test_an_unknown_option_exits_2(project: pathlib.Path, tmp_path: pathlib.Path) -> None:
    with pytest.raises(SystemExit) as raised:
        run(project, tmp_path / 'home', '--nope')
    assert raised.value.code == 2


def test_a_dangling_link_is_reported_with_its_rm_line(project: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / 'home' / '.claude'
    (target / 'skills').mkdir(parents=True)
    (target / 'skills' / 'old').symlink_to(tmp_path / 'gone')
    assert run(project, target) == 0
    out = capsys.readouterr().out
    assert 'Dangling symlinks found:' in out
    assert f'rm {target.resolve() / "skills" / "old"}' in out
    assert (target / 'skills' / 'old').is_symlink()


def test_links_resolve_when_the_target_is_reached_through_a_symlink(project: pathlib.Path, tmp_path: pathlib.Path) -> None:
    real = tmp_path / 'real-home'
    real.mkdir()
    # Deeper than the real directory, so a link computed from the alias's own
    # path would climb the wrong number of levels.
    alias = tmp_path / 'a' / 'b' / 'alias-home'
    alias.parent.mkdir(parents=True)
    alias.symlink_to(real)
    assert run(project, alias / '.claude') == 0
    assert (real / '.claude' / 'CLAUDE.md').read_text() == 'top\n'
    assert (real / '.claude' / 'skills' / 'probe' / 'SKILL.md').read_text() == 'probe\n'


def test_set_if_absent_applies_before_append(project: pathlib.Path, tmp_path: pathlib.Path) -> None:
    target = tmp_path / 'home' / '.claude'
    assert run(project, target, '--append', 'xs=1', '--set-if-absent', 'xs=[0]') == 0
    assert json.loads((target / 'settings.json').read_text()) == {'xs': [0, 1]}
