Audit whether this repository's user docs, under docs/, agree with its
knowledge bundle, .okf/ (decisions, architecture pages, practices and the
manifesto; not handoffs or the log). This is not a check against the code:
another audit does that. Look for places where the two say different
things about the same subject.

1. Read every page in docs/ and list the subjects it makes claims about:
   what a part does, why something works as it does, what is supported or
   out of scope, defaults, names, steps.
2. For each subject, find what .okf/ says about it with search_files, and
   read those lines. A decision's Correction sections amend it, and a
   superseded decision is replaced by its successor.
3. Put each docs page in checked, naming the concepts you compared it
   against. Make a finding for each subject where they disagree: the claim
   is the docs line, contradicted_by the .okf/ lines, and the fix says
   which side looks out of date (check the code when you need to decide)
   and what it should say.

A subject the docs cover and .okf/ does not is not a finding. Every docs
page gets a checked entry, and the summary says how many pages and
subjects you compared.
