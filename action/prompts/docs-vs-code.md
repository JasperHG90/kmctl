Audit this repository's user docs against its code: every page under docs/
(skip images and other files that are not text).

For each page:

1. Read the whole page. List its concrete claims: commands, options and
   their defaults, file paths, config keys, inputs, environment variables,
   exit codes, output it says a command prints, and steps it says will work.
2. Check each claim against the code that decides it. Find the code with
   search_files (the option's name, the key, the path), then read the lines
   that define it. Where a page shows a command's --help or output, find the
   source that produces it; you may also run the command with run_shell to
   see it, but cite the source lines, since the report only accepts lines
   you read or found by search.
3. Put the page in checked, saying what you compared it against. Make a
   finding for each claim the code contradicts: the claim is the page's
   line, contradicted_by the code's lines, and the fix says what the page
   should say.

Judge only what a page claims, not its style or what it leaves out. A claim
you could not find the code for is a medium finding that says what you
searched for. Do not stop at the first few pages: every page gets a checked
entry, and the summary says how many pages and claims you checked.
