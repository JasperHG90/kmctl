"""The check-writing instructions ``kmaudit checks todo --json`` hands an agent, once, with the answer's schema."""

INSTRUCTIONS = """
You turn claims about a repository into checks. A check is a list of steps
that kmaudit later runs against the repository with no model, every time the
files it reads change, so a good check saves a model call forever. A check
holds when every step holds.

Steps (the answer schema gives every field):
- file: a tracked path or glob exists (exists: true) or does not (false).
- grep: a Python regex matches some line (present: true) or none (false) in a
  glob of files.
- code: code of a given shape appears in a glob of source files (Python,
  shell, JavaScript, TypeScript, Rust, Java, Ruby). Write the code as it would
  appear, with $NAME for any one expression and $$$NAME for any run of
  arguments or statements: subprocess.run($$$A, timeout=120), if not $X:
  $$$B, sys.exit(1). It never matches comments or strings and ignores line
  breaks. It must be a whole expression or statement: f($$$A, timeout=120),
  not timeout=120. It tests presence only: test absence with grep.
- query: a JMESPath query over YAML, TOML or JSON files; expect equals,
  every, contains, not_empty or empty.
- definition: a Python function, class or assigned name is defined (or not)
  in a glob of Python files.
- imports: a Python file imports a top-level module (or not).
- help: a command of the repository's own CLI prints --help text matching a
  regex (or not).

Rules:
- A check must fail if the claim were false. Test what the claim says, not a
  word from it: "the default --min-severity is high" needs the default, not
  just the flag.
- To test what code does, prefer code over grep: a call and its argument, a
  condition and its exit. Use grep for text in files no code step reads.
- Markdown files, the folder being audited, .okf/ and docs/ are never read:
  they restate the claims.
- Prefer one or two narrow steps over many loose ones. Pin a regex to the code
  that does the thing, not to a comment or docstring.
- strength "exact": the steps decide the claim. "proxy": they show the code
  the claim is about exists in the shape the claim needs, but behaviour still
  has to be read (say what in why).
- When no step can test a claim (behaviour across several files, what a
  runner or person does, history, intent), give a reason instead of a check.
  A proxy that tests nothing the claim says is worse than a reason.
- Scope each step to the files the claim is about. To test one job or step of
  a YAML file, use query (jobs.audit.steps[].env), not grep over the file.
- In JMESPath, quote a key with a hyphen: steps[].with."persist-credentials".
  Guard a function against a missing key: [?uses && starts_with(uses, 'x')].
  YAML reads a workflow's on: key as true, so test triggers with grep.

Try before you submit. Pipe a draft to kmaudit checks try - --json: it
runs the steps, says whether each holds and what it saw, and changes the code
it matched in memory (flip a boolean, change a number or string, negate a
condition, delete a statement) to see whether the check notices. A check
that holds but notices none of those changes is weak: it tests a comment, a
name, or nothing the claim depends on. kmaudit checks submit refuses a
weak check, naming the changes it missed; pin it to the code that does the
thing instead.

A check that fails may mean the claim is wrong. Look once more; do not bend
the check until it holds. If the claim is wrong, submit the check that tests
it with drift set to one sentence saying what the code does instead.

Answer each claim with one JSON object, and pipe a list of them to
kmaudit checks submit -:

{"claim": "<claim id from todo>", "steps": [{"op": "code", "pattern":
 "sys.exit(1)", "paths": "src/tool/cli.py"}], "strength": "exact",
 "why": "One sentence: why these steps hold exactly when the claim does."}

{"claim": "<claim id>", "reason": "One sentence: why no step can test it."}
""".strip()
