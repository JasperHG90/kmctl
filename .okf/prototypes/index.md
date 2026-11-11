# Prototypes
- [Audit agent](audit-agent/README.md): Spike for the audit agent: read a repository, chunk the .okf/ bundle and extract checkable claims with an LLM.
- [Audit CLI](audit-cli/README.md): The audit agent's claim extraction as a Typer CLI: audit claims extract or diff a bundle or one concept file, into a per-project SQLite database, set by audit.toml.
