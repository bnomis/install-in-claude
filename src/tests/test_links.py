import os
import pathlib

import pytest

import install_in_claude.links


@pytest.fixture
def dirs(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    source = tmp_path / 'repo' / 'claude'
    (source / 'skills' / 'probe').mkdir(parents=True)
    (source / 'skills' / 'probe' / 'SKILL.md').write_text('probe\n')
    (source / 'rules').mkdir()
    (source / 'rules' / 'a.md').write_text('a\n')
    (source / 'CLAUDE.md').write_text('top\n')
    (source / '.hidden').write_text('skip\n')
    return source, tmp_path / 'home' / '.claude'


def test_links_files_and_directories_one_level_down(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    install_in_claude.links.link_entries(source, target, dry_run=False)
    assert (target / 'CLAUDE.md').is_symlink()
    assert (target / 'skills').is_dir() and not (target / 'skills').is_symlink()
    assert (target / 'skills' / 'probe').is_symlink()
    assert (target / 'skills' / 'probe' / 'SKILL.md').read_text() == 'probe\n'
    assert (target / 'rules' / 'a.md').read_text() == 'a\n'
    assert not (target / '.hidden').exists()


def test_every_link_is_relative(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    install_in_claude.links.link_entries(source, target, dry_run=False)
    for link in [target / 'CLAUDE.md', target / 'skills' / 'probe', target / 'rules' / 'a.md']:
        assert not os.readlink(link).startswith('/')


def test_an_existing_link_is_replaced(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    target.mkdir(parents=True)
    (target / 'CLAUDE.md').symlink_to('/nowhere')
    install_in_claude.links.link_entries(source, target, dry_run=False)
    assert (target / 'CLAUDE.md').read_text() == 'top\n'


def test_a_real_file_is_renamed_orig_then_orig_2(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    target.mkdir(parents=True)
    (target / 'CLAUDE.md').write_text('mine\n')
    (target / 'CLAUDE.md.orig').write_text('older\n')
    install_in_claude.links.link_entries(source, target, dry_run=False)
    assert (target / 'CLAUDE.md.orig').read_text() == 'older\n'
    assert (target / 'CLAUDE.md.orig.2').read_text() == 'mine\n'
    assert (target / 'CLAUDE.md').is_symlink()


def test_a_second_run_changes_nothing(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    first = install_in_claude.links.link_entries(source, target, dry_run=False)
    before = sorted((p, os.readlink(p)) for p in target.rglob('*') if p.is_symlink())
    second = install_in_claude.links.link_entries(source, target, dry_run=False)
    after = sorted((p, os.readlink(p)) for p in target.rglob('*') if p.is_symlink())
    assert before == after
    assert first == second
    assert not list(target.rglob('*.orig'))


def test_a_dry_run_changes_nothing(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    messages = install_in_claude.links.link_entries(source, target, dry_run=True)
    assert not target.exists()
    assert messages and all(message.startswith('Would link ') for message in messages)


def test_messages_name_source_destination_and_relative_path(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    messages = install_in_claude.links.link_entries(source, target, dry_run=False)
    assert f'Linking {source / "CLAUDE.md"} to {target / "CLAUDE.md"} via ../../repo/claude/CLAUDE.md' in messages


def test_a_dangling_link_is_found(tmp_path: pathlib.Path) -> None:
    (tmp_path / 'skills').mkdir()
    (tmp_path / 'skills' / 'gone').symlink_to(tmp_path / 'missing')
    (tmp_path / 'skills' / 'here').symlink_to(tmp_path / 'skills')
    assert install_in_claude.links.dangling_links(tmp_path) == [tmp_path / 'skills' / 'gone']


def test_no_dangling_links_when_all_resolve(dirs: tuple[pathlib.Path, pathlib.Path]) -> None:
    source, target = dirs
    install_in_claude.links.link_entries(source, target, dry_run=False)
    assert install_in_claude.links.dangling_links(target) == []


def test_nothing_below_max_depth_is_reported(tmp_path: pathlib.Path) -> None:
    (tmp_path / 'a' / 'b').mkdir(parents=True)
    (tmp_path / 'a' / 'b' / 'gone').symlink_to(tmp_path / 'missing')
    assert install_in_claude.links.dangling_links(tmp_path) == []
    assert install_in_claude.links.dangling_links(tmp_path, max_depth=3) == [tmp_path / 'a' / 'b' / 'gone']


def test_a_missing_target_has_no_dangling_links(tmp_path: pathlib.Path) -> None:
    assert install_in_claude.links.dangling_links(tmp_path / 'absent') == []
