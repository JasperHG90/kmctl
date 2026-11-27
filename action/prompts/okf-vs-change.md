Audit the decisions a change may have outdated. The repository is checked
out at the change, and the list under "Decisions in scope" below names each
stable decision in .okf/decisions/ whose sources cover a file the change
touched, with those files.

You have the read, search and list tools; do not rely on a shell or on the
scripts a skill ships. Report only: never change, commit or push a file.

For each decision in scope:

1. Read the whole decision, including any Correction sections, which amend
   it.
2. Read the changed files it lists, and the lines in them that bear on what
   the decision says.
3. Decide whether the decision still holds after the change. Check each
   claim it makes about those files: names, defaults, steps, which part does
   what.
4. Put the decision in checked, saying which changed files you compared it
   against. Make a finding for each claim the change contradicts: the claim
   is the decision's line, contradicted_by the changed code's lines, and the
   fix says what to do: a Correction section, a new decision that supersedes
   it, or a change to the code. A decision is never edited in its body.

You may add another decision that the change affects though its sources do
not name a changed file. Say for each one why the change affects it, in its
checked entry or finding.

When the list says no decision is in scope, say so in the summary, check
nothing else, and make no finding. The summary says how many decisions you
checked and how many claims.
