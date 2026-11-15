"""Ask Clef the outside question again, this time with the code the tracer cited, for every labelled claim the outside rule sent to not code.

Run from the prototype folder: python3 scripts/outside_with_code.py
Needs BIFROST_CC_VIRTUAL_KEY. Prints Clef's probability next to each label, so you can see whether it separates them.
"""
import asyncio, contextlib, io, json, os
import httpx

URL = "https://bifrost.lab.orangecluster.nl/v1/decisions"
QUESTION = {"code_settles": {"type": "noul", "instructions": (
    "Answer yes if the code quoted under 'evidence' is enough on its own to show the claim is true or false: the claim is "
    "about what this repository's code, config or files contain or do. Answer no if judging the claim needs knowledge "
    "of how an outside tool, service or platform behaves (for example what a registry does with a tag, or how a runner "
    "schedules jobs), which no file in the repository shows.")}}


def cases():
    out = []
    ns = {"__file__": "scripts/score_labels.py"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(open("scripts/score_labels.py").read().split("POS = ")[0].replace("sys.argv[1]", repr("results/ties/kmctl/final-2026-11-08.json")), ns)
    for i, (label, _) in ns["labels"].items():
        t = ns["ties"].get(i)
        if t and t["status"] == "not code" and "likely about what a tool outside" in t["note"]:
            out.append(("kmctl", label, t))
    ties = {t["claim_id"]: t for t in json.load(open("results/ties/localstack/3f9d24f2-dirty.json"))["ties"]}
    for l in json.load(open("labels/localstack_rand_out_0.json")):
        t = ties.get(l["id"])
        if t and t["status"] == "not code" and "likely about what a tool outside" in t["note"]:
            out.append(("localstack", l["verdict"], t))
    return out


async def ask(client, t):
    evidence = t["evidence"] if isinstance(t["evidence"], list) else []
    state = {"claim": t["claim"], "sentence": t["sentence"],
             "evidence": [f"{e['path']}:{e.get('line')}: {e.get('quote', '')[:600]}" for e in evidence[:3]] or t.get("sites", [])[:5],
             "tracer said": t["note"].split("; ", 1)[-1][:500]}
    r = await client.post(URL, headers={"Authorization": "Bearer " + os.environ["BIFROST_CC_VIRTUAL_KEY"]},
                          json={"model": "ollama/clef:27b", "state": state, "questions": QUESTION})
    r.raise_for_status()
    return r.json()["answers"]["code_settles"]["value"]


async def main():
    async with httpx.AsyncClient(timeout=120) as client:
        rows = cases()
        ps = await asyncio.gather(*(ask(client, t) for _, _, t in rows))
    for (repo, label, t), p in sorted(zip(rows, ps), key=lambda x: -x[1]):
        print(f"{p:.2f} {label:10} {repo:10} {t['claim'][:90]}")

asyncio.run(main())
