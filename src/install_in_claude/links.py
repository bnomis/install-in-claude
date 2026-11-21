"""Linking a project's Claude Code files into a target directory."""

import pathlib


def free_path(dst: pathlib.Path) -> pathlib.Path:
    """The first of `<name>.orig`, `<name>.orig.2`, ... that does not exist."""
    candidate = dst.with_name(f'{dst.name}.orig')
    i = 2
    while candidate.exists() or candidate.is_symlink():
        candidate = dst.with_name(f'{dst.name}.orig.{i}')
        i += 1
    return candidate


def link_one(src: pathlib.Path, dst: pathlib.Path, dry_run: bool) -> str:
    """Link dst to src relatively; replace a link in the way, rename a real file to .orig."""
    relative = src.parent.relative_to(dst.parent, walk_up=True) / src.name
    if dry_run:
        return f'Would link {src} to {dst} via {relative}'
    if dst.is_symlink():
        dst.unlink()
    elif dst.exists():
        dst.rename(free_path(dst))
    dst.symlink_to(relative)
    return f'Linking {src} to {dst} via {relative}'


def link_entries(source: pathlib.Path, target: pathlib.Path, dry_run: bool) -> list[str]:
    """Link each entry of source into target; returns one message per link.

    A top-level file is linked as `target/<name>`; a top-level directory is
    created in target and each of its entries is linked into it, one level
    only. Top-level entries starting with '.' are skipped.
    """
    messages = []
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source.iterdir()):
        if entry.name.startswith('.'):
            continue
        dest = target / entry.name
        if not entry.is_dir():
            messages.append(link_one(entry, dest, dry_run))
            continue
        if not dry_run:
            dest.mkdir(parents=True, exist_ok=True)
        messages.extend(link_one(child, dest / child.name, dry_run) for child in sorted(entry.iterdir()))
    return messages


def dangling_links(target: pathlib.Path, max_depth: int = 2) -> list[pathlib.Path]:
    """Symlinks under target, at most max_depth levels down, whose target is gone."""
    if not target.is_dir():
        return []
    root_depth = len(target.parts)
    found = []
    for dirpath, dirnames, filenames in target.walk(top_down=True):
        if len(dirpath.parts) - root_depth >= max_depth - 1:
            dirnames.clear()
        for name in filenames:
            path = dirpath / name
            if path.is_symlink() and not path.exists():
                found.append(path)
    return sorted(found)
