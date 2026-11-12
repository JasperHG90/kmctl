# Prototypes
- [Audit agent](audit-agent/README.md): Spike for the audit agent: read a repository, chunk the .okf/ bundle and extract checkable claims with an LLM.
- [Audit CLI](audit-cli/README.md): The audit agent's claim extraction as a Typer CLI: audit claims extract or diff a bundle or one concept file, into a per-project SQLite database, set by audit.toml.
- [Audit UI](audit-ui/README.md): A starter page for browsing kmctl audit results: documents that need a new audit, each sentence coloured by whether its claims are checked, and the selected text's claims, checks and confidence.
- [Mixed claims](mixed-claims/README.md): A count of how many claims answered with a reason join a checkable fact to an opinion: 1 of 384 on a strict reading, 3 on a loose one, so a split rule for the extractor is not worth a ticket.
