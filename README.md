<p align="center">
  <img src="docs/assets/logo.png" alt="kmctl logo: an owl with glasses holding a folder, next to the word kmctl" width="480">
</p>

# kmctl

This repository keeps a project's knowledge current and checks it against
the code. It holds two packages in one uv workspace. They work well
together and install apart.

## Packages

- **[kmctl](packages/kmctl/README.md)** keeps `docs/` and an `.okf/`
  knowledge bundle current through your coding agent, with a CLI, an APM
  package of skills and rules, and a GitHub Action.
- **[kmaudit](packages/kmaudit/README.md)** checks what a folder of markdown
  docs claims against the code: an agent lists the claims and writes a check
  for each, and kmaudit reruns the checks with no model.

Each package's README says how to install and use it.

## Documentation

[`docs/`](docs/README.md) holds the pages for people who use kmctl and
kmaudit: tutorials, how-to guides, reference and explanation.

## Working on this repository

Start at [`.okf/summary.md`](.okf/summary.md), which links down to the rest
of the bundle; the design is [`.okf/manifesto.md`](.okf/manifesto.md) and
the reasons for each choice are in [`.okf/decisions/`](.okf/decisions/index.md).

`uv sync` at the root installs both packages, since kmaudit is a workspace
member. `just lint`, `just test` and `just integration` run the checks for
both, the root `pytest` running kmaudit's tests under
`packages/kmaudit/tests/` too. `just hooks` installs the pre-commit hooks in
`.pre-commit-config.yaml`.

Changes go through the loop: each ticket has a plan, a signed eval and a
review round in `.loop/`, and `loopctl gate stamp` runs the gates listed in
`.loop/config.toml`. [`CLAUDE.md`](CLAUDE.md) says where each kind of
knowledge lives and `.claude/rules/` holds the rules for working here.
