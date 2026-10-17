# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pydantic-ai-slim[openai]==2.57.0",
#   "opentelemetry-sdk==1.45.1",
#   "opentelemetry-exporter-otlp-proto-http==1.45.1",
#   "httpx",
# ]
# ///
"""Replay a real audit transcript through PydanticAI into a live Langfuse project, then read it back.

Usage: replay.py TRANSCRIPT [--batch N] [--no-content]
Exits 0 only when Langfuse holds every span as an observation and every chat
span shows input, output, model and usage, with no exporter error.
Keys come from LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL.
"""

import argparse
import base64
import json
import logging
import os
import sys
import time
import uuid

import httpx
from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelRequest, ModelResponse, RetryPromptPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.usage import UsageLimits

ap = argparse.ArgumentParser()
ap.add_argument("transcript")
ap.add_argument("--batch", type=int, default=512, help="BatchSpanProcessor max_export_batch_size")
ap.add_argument("--no-content", action="store_true")
args = ap.parse_args()

BASE = os.environ["LANGFUSE_BASE_URL"].rstrip("/")
AUTH = "Basic " + base64.b64encode(
    f"{os.environ['LANGFUSE_PUBLIC_KEY']}:{os.environ['LANGFUSE_SECRET_KEY']}".encode()
).decode()

# --- capture exporter warnings/errors
records: list[str] = []


class Grab(logging.Handler):
    def emit(self, r):
        records.append(f"{r.name} {r.levelname}: {r.getMessage()[:400]}")


h = Grab(level=logging.WARNING)
for name in ("opentelemetry", "opentelemetry.exporter", "opentelemetry.sdk"):
    logging.getLogger(name).addHandler(h)
    logging.getLogger(name).setLevel(logging.WARNING)

# --- load the transcript
messages = ModelMessagesTypeAdapter.validate_json(open(args.transcript, "rb").read())
responses = [m for m in messages if isinstance(m, ModelResponse)]
first = messages[0]
assert isinstance(first, ModelRequest)
prompt = "".join(p.content for p in first.parts if p.part_kind == "user-prompt")
instructions = first.instructions
returns = {
    p.tool_call_id: p.content
    for m in messages
    if isinstance(m, ModelRequest)
    for p in m.parts
    if isinstance(p, ToolReturnPart)
}
retries = [
    p.content
    for m in messages
    if isinstance(m, ModelRequest)
    for p in m.parts
    if isinstance(p, RetryPromptPart) and p.tool_name == "final_result"
]
print(f"transcript: {len(messages)} messages, {len(responses)} model requests, "
      f"{len(returns)} tool returns, {len(retries)} final_result retries, "
      f"model={responses[0].model_name}")

# --- the replay model: turn i returns recorded response i
turn = {"i": 0}


def model_fn(msgs, info: AgentInfo) -> ModelResponse:
    r = responses[turn["i"]]
    turn["i"] += 1
    return ModelResponse(parts=r.parts, usage=r.usage, model_name=r.model_name)


def make_tool(name):
    def fn(ctx: RunContext, **kw):
        return returns[ctx.tool_call_id]

    return Tool.from_schema(fn, name=name, description=f"stub {name}",
                            json_schema={"type": "object", "additionalProperties": True}, takes_ctx=True)


class Report(BaseModel):
    model_config = ConfigDict(extra="allow")


marker = f"kmctl-spike-{uuid.uuid4().hex[:8]}"


# --- exporter wrapper: sum serialized bytes, record results
class Counting(OTLPSpanExporter):
    sent_bytes = 0
    batches: list[tuple[int, int, str]] = []
    spans: list = []

    def export(self, spans):
        n = len(encode_spans(spans).SerializeToString())
        res = super().export(spans)
        Counting.sent_bytes += n
        Counting.batches.append((len(spans), n, res.name))
        Counting.spans.extend(spans)
        return res


exporter = Counting(endpoint=BASE + "/api/public/otel/v1/traces", headers={"Authorization": AUTH}, timeout=60)
provider = TracerProvider(resource=Resource.create({"service.name": marker}))
provider.add_span_processor(BatchSpanProcessor(exporter, max_export_batch_size=args.batch,
                                               max_queue_size=max(2048, args.batch)))
settings = InstrumentationSettings(tracer_provider=provider, include_content=not args.no_content)

retry_iter = iter(retries)
agent = Agent(
    FunctionModel(model_fn, model_name=responses[0].model_name or "replay"),
    name=marker,
    instructions=instructions,
    output_type=Report,
    tools=[make_tool(n) for n in ("read_file", "search_files", "list_files", "run_shell")],
    capabilities=[Instrumentation(settings=settings)],
)


@agent.output_validator
def replay_retry(out: Report) -> Report:
    msg = next(retry_iter, None)
    if msg is not None:
        raise ModelRetry(msg)
    return out


result = agent.run_sync(prompt, usage_limits=UsageLimits(request_limit=200))
print(f"replayed {turn['i']} model turns; output keys={list(result.output.model_dump())[:5]}")
t0 = time.time()
provider.shutdown()
print(f"export: {len(Counting.spans)} spans in {len(Counting.batches)} requests, "
      f"{Counting.sent_bytes / 1e6:.2f} MB protobuf, flush {time.time() - t0:.1f}s")
bad = [b for b in Counting.batches if b[2] != "SUCCESS"]
print(f"largest request {max(b[1] for b in Counting.batches) / 1e6:.2f} MB; failed requests: {bad}")
for r in records:
    print("LOG", r)

spans = Counting.spans
trace_ids = {format(s.context.trace_id, "032x") for s in spans}
assert len(trace_ids) == 1, trace_ids
trace_id = trace_ids.pop()
chats = [s for s in spans if s.name.startswith("chat")]
in_size = {format(s.context.span_id, "016x"): len(str((s.attributes or {}).get("gen_ai.input.messages", "")))
           for s in chats}
print(f"trace_id={trace_id} marker={marker} spans={len(spans)} chat={len(chats)} "
      f"largest input attr={max(in_size.values()) / 1e6:.2f} MB, sum chat input attrs={sum(in_size.values()) / 1e6:.2f} MB")

# --- read back from Langfuse
cli = httpx.Client(base_url=BASE, headers={"Authorization": AUTH}, timeout=60)


def get(url, **kw):
    for attempt in range(8):
        r = cli.get(url, **kw)
        if r.status_code != 429:
            return r
        wait = float(r.headers.get("retry-after") or 15 * (attempt + 1))
        print(f"readback 429 on {url}, waiting {wait:.0f}s")
        time.sleep(wait)
    return r


def observations():
    out, page = [], 1
    while True:
        r = get("/api/public/observations", params={"traceId": trace_id, "limit": 100, "page": page})
        r.raise_for_status()
        j = r.json()
        out += j["data"]
        if page >= j["meta"].get("totalPages", 1) or not j["data"]:
            return out
        page += 1


obs, deadline = [], time.time() + 240
time.sleep(20)  # first ingestion pass
while time.time() < deadline:
    try:
        obs = observations()
    except httpx.HTTPStatusError as e:
        print(f"readback HTTP {e.response.status_code}: {e.response.text[:200]}")
    if len(obs) >= len(spans):
        time.sleep(15)  # let late updates land, then read once more
        obs = observations()
        break
    time.sleep(30)
print(f"observations found={len(obs)} of {len(spans)} spans after {time.time() - deadline + 240:.0f}s")
tr = get(f"/api/public/traces/{trace_id}")
print(f"trace GET {tr.status_code}; name={tr.json().get('name') if tr.is_success else None}")

found = {o["id"]: o for o in obs}
missing = [s.name for s in spans if format(s.context.span_id, "016x") not in found]
print(f"missing spans: {len(missing)} {missing[:10]}")
gens = [found[i] for i in in_size if i in found]
problems = []
for sid in sorted(in_size, key=in_size.get, reverse=True):
    o = found.get(sid)
    if o is None:
        problems.append(f"{sid} missing")
        continue
    inp, outp = o.get("input"), o.get("output")
    usage = o.get("usageDetails") or o.get("usage") or {}
    in_len = len(json.dumps(inp)) if inp is not None else 0
    ok = bool(inp) and bool(outp) and bool(o.get("model")) and any((v or 0) > 0 for v in usage.values() if isinstance(v, (int, float)))
    if not args.no_content and in_len < 0.9 * in_size[sid]:
        ok = False
    if not ok:
        problems.append(f"{sid} type={o.get('type')} model={o.get('model')} in_len={in_len}/{in_size[sid]} "
                        f"out={'yes' if outp else 'no'} usage={usage}")
top = sorted(in_size, key=in_size.get, reverse=True)[:3]
for sid in top:
    o = found.get(sid) or {}
    print(f"top chat {sid}: sent {in_size[sid] / 1e3:.0f} kB; type={o.get('type')} model={o.get('model')} "
          f"input={len(json.dumps(o.get('input'))) / 1e3 if o.get('input') is not None else 0:.0f} kB "
          f"output={'yes' if o.get('output') else 'no'} usageDetails={o.get('usageDetails')}")
print(f"chat spans with a problem: {len(problems)}")
for p in problems[:15]:
    print("PROBLEM", p)
print(f"URL {BASE}/trace/{trace_id}  (project url: open via the Langfuse UI; trace id {trace_id})")
ok = not bad and not records and not missing and not problems
sys.exit(0 if ok else 1)
