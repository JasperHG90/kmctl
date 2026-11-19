<p align="center">
  <img src="docs/assets/logo.png" alt="kmctl logo: an owl with glasses holding a folder, next to the word kmctl" width="480">
</p>

# kmctl

[![CI](https://github.com/JasperHG90/kmctl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JasperHG90/kmctl/actions/workflows/ci.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/github/license/JasperHG90/kmctl)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)

This repository keeps a project's knowledge current and checks it against
the code. It holds two packages in one uv workspace. They work well
together and install apart.

## Packages

- **[kmctl](packages/kmctl/README.md)**
  ![Lifecycle: stable](https://img.shields.io/badge/lifecycle-stable-brightgreen)
  [![kmctl release](https://img.shields.io/github/v/release/JasperHG90/kmctl?filter=v*&sort=semver&label=release)](https://github.com/JasperHG90/kmctl/releases/latest)
  starts from the code and the decisions and keeps `docs/` and an `.okf/`
  knowledge bundle current through your coding agent, with a CLI, an APM
  package of skills and rules, and a GitHub Action.
- **[kmaudit](packages/kmaudit/README.md)**
  ![Lifecycle: beta](https://img.shields.io/badge/lifecycle-beta-orange)
  [![kmaudit release](https://img.shields.io/github/v/release/JasperHG90/kmctl?filter=kmaudit-v*&sort=semver&label=release)](https://github.com/JasperHG90/kmctl/releases?q=kmaudit-v)
  is in beta. It starts from a folder of markdown docs and checks what they
  claim against the code. It runs inside your coding agent's harness: the
  agent's model lists the claims and writes a check for each, and kmaudit
  reruns the checks as plain code, with no model.

A feature goes in the package whose direction it shares
([ADR 0046](.okf/decisions/0046-kmctl-works-from-code-toward-knowledge-and-kmaudit-from-knowledge-toward-code.md)). Each package's README says how
to install and use it.

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
