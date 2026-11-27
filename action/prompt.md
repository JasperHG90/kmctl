Reread the pages a pull request may have outdated. The repository is checked
out at the pull request, and the list under "Pages in scope" below names each
page under .okf/ or docs/ whose sources cover a file the pull request
changed, with its status and those files.

For each page in scope:

1. Read the whole page. A decision's Correction sections amend it; read
   them too.
2. Read the changed files it lists, and the lines in them that bear on what
   the page says.
3. Check each claim the page makes about those files: names, options and
   their defaults, steps, paths, which part does what. Find the lines that
   decide it with search_files, then read them.
4. Put the page in checked, with its path as the subject and the changed
   files you compared it with as against. Make a finding for each claim the change contradicts: the claim
   is the page's line, contradicted_by the changed code's lines, and the fix
   says what to do.

What a fix says depends on the page:

- A stable decision is never edited in its body. The fix is a dated
  Correction section appended to it, a new decision that supersedes it, or a
  change to the code. A new decision starts as a draft
  (`kmctl new decision --draft`), and only the pull request's author accepts
  it; never suggest accepting one for them.
- A draft decision the pull request adds can still change: say what to
  change in it before the author accepts it, or that it contradicts a stable
  decision it should supersede.
- Any other page (an architecture page, a practice, a docs page) is edited
  to match the code.
- After a Correction or an edit to a page under .okf/, the fix adds: run
  `kmctl summary ack` if .okf/summary.md still holds, since a summary behind
  its concepts fails the pull request's check.

Keep the report short; the comment shows the first sentence of each field
and folds the rest away:

- summary: one or two sentences on what the change does to the pages. Do
  not list the pages that hold or a command: the comment lists them.
- each checked entry: subject is the page's path and nothing else; against
  names the changed files you compared it with.
- each finding: title in a few words, summary in one sentence, fix in one
  sentence.

Never run `kmctl verify ID ID ... --by human:<their id>` yourself, and never
claim a page was verified; the comment offers that command for the pages
that hold, for the author to run once they have read them.

You may add a page the change affects though its sources do not name a
changed file. Say why the change affects it in its checked entry's against,
or in its finding.
