# install-in-claude

`install-in-claude` links a project's Claude Code files into `~/.claude/` and
merges the `settings.json` entries the project needs, with every
project-specific setting given on the command line. The design is
`agents/specs/install-in-claude/spec.md`.

## Tests

From the repository root:

```shell
source bin/activate.sh && pytest src/tests -q
```

## Hooks

Install all three hook types after cloning:

```shell
pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
```

## No project names

This repository serves many projects. Its code, tests, fixtures, specs, task
lists, records and commit messages name no project it has been run on: a
project it serves is "one project", described by what it does. The
`no-project-names` hook, published by the agents repository, enforces it at
commit and commit-msg time.
