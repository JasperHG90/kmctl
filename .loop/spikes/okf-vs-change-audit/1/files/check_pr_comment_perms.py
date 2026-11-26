"""Does GitHub's docs say `pull-requests` (no `issues`) covers list/create/edit of PR comments?

GITHUB_TOKEN's `permissions:` keys map to GitHub App repository permissions
(workflow-syntax docs link `pull-requests` to the GitHub Apps permissions page).
Fetch that page and check that the three
endpoints publish uses are listed under "Pull requests" at the needed level.
Exits 0 when pull-requests: write is enough, 1 otherwise.
"""

import re
import sys
import urllib.request

BASE = "https://docs.github.com/api/article/body?pathname="


def fetch(path: str) -> str:
    with urllib.request.urlopen(BASE + path, timeout=20) as resp:
        return resp.read().decode()


def section(doc: str, title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## )", doc, re.S | re.M)
    return m.group(1) if m else ""


apps = fetch("/en/rest/authentication/permissions-required-for-github-apps")
pr = section(apps, 'Repository permissions for "Pull requests"')
needed = {
    "GET /repos/{owner}/{repo}/issues/{issue_number}/comments": "read",
    "POST /repos/{owner}/{repo}/issues/{issue_number}/comments": "write",
    "PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}": "write",
}
ok = bool(pr)
for endpoint, level in needed.items():
    row = next((line for line in pr.splitlines() if f"`{endpoint}`" in line), None)
    print(f"Pull requests section: {endpoint}: {row or 'MISSING'}")
    if row is None or f"| {level} |" not in row:
        ok = False

print("pull-requests: write is enough" if ok else "pull-requests: write is NOT enough")
sys.exit(0 if ok else 1)
