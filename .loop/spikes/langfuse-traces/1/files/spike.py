# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pydantic-ai-slim[openai]==2.57.0",
#   "opentelemetry-sdk==1.45.1",
#   "opentelemetry-exporter-otlp-proto-http==1.45.1",
# ]
# ///
"""Does PydanticAI 2.57 + a plain TracerProvider emit the gen_ai.* attributes Langfuse maps?

Exits 0 only when every required attribute is present.
"""

import base64
import importlib.metadata as md
import sys

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.instrumented import InstrumentationSettings

for pkg in ("pydantic-ai-slim", "opentelemetry-sdk", "opentelemetry-exporter-otlp-proto-http", "logfire", "logfire-api"):
    try:
        print(f"version {pkg}={md.version(pkg)}")
    except md.PackageNotFoundError:
        print(f"version {pkg}=not installed")

s0 = InstrumentationSettings()
print(f"defaults: version={s0.version} include_content={s0.include_content}")


class Finding(BaseModel):
    claim: str
    ok: bool


def model_fn(messages, info: AgentInfo) -> ModelResponse:
    returned = any(isinstance(p, ToolReturnPart) for m in messages for p in getattr(m, "parts", []))
    if not returned:
        return ModelResponse(parts=[ToolCallPart("read_file", {"path": "README.md"})])
    out_tool = info.output_tools[0].name
    return ModelResponse(parts=[ToolCallPart(out_tool, {"claim": "readme exists", "ok": True})])


exporter = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))


def read_file(path: str) -> str:
    """Read a file."""
    return f"contents of {path}"


agent = Agent(
    FunctionModel(model_fn, model_name="fake-model"),
    output_type=Finding,
    tools=[read_file],
    capabilities=[Instrumentation(settings=InstrumentationSettings(tracer_provider=provider))],
)
result = agent.run_sync("check the readme")
print(f"output: {result.output!r}")

spans = exporter.get_finished_spans()
by_id = {s.context.span_id: s.name for s in spans}
for s in spans:
    parent = by_id.get(s.parent.span_id, "?") if s.parent else None
    print(f"\n== span {s.name!r} parent={parent!r}")
    for k, v in (s.attributes or {}).items():
        print(f"   {k} = {str(v)[:120]}")
    for e in s.events:
        print(f"   event {e.name}: {list((e.attributes or {}).keys())}")

all_keys = {}
for s in spans:
    for k in s.attributes or {}:
        all_keys.setdefault(k, []).append(s.name)

required = {
    "agent root span (no parent)": any(s.parent is None for s in spans),
    "gen_ai.request.model on a chat span": any(
        s.name.startswith("chat") and "gen_ai.request.model" in (s.attributes or {}) for s in spans
    ),
    "gen_ai.usage.input_tokens": "gen_ai.usage.input_tokens" in all_keys,
    "gen_ai.usage.output_tokens": "gen_ai.usage.output_tokens" in all_keys,
    "gen_ai.input.messages": "gen_ai.input.messages" in all_keys,
    "gen_ai.output.messages": "gen_ai.output.messages" in all_keys,
    "tool span with gen_ai.tool.name": any("gen_ai.tool.name" in (s.attributes or {}) for s in spans),
    "tool call arguments attribute": any(
        k in all_keys for k in ("gen_ai.tool.call.arguments", "tool_arguments")
    ),
    "tool call result attribute": any(k in all_keys for k in ("gen_ai.tool.call.result", "tool_response")),
}
print("\n== checks")
for name, ok in required.items():
    print(f"   {'PASS' if ok else 'FAIL'} {name}")

print(f"\nlogfire in sys.modules: {'logfire' in sys.modules}; logfire_api in sys.modules: {'logfire_api' in sys.modules}")

# OTLP exporter for Langfuse, built but never exporting (no spans go through it).
auth = base64.b64encode(b"pk-lf-x:sk-lf-y").decode()
otlp = OTLPSpanExporter(
    endpoint="https://cloud.langfuse.com/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {auth}"},
)
print(f"otlp endpoint={otlp._endpoint} auth header set={otlp._client._headers.get('authorization', '').startswith('Basic ')}")

# Shutdown flush: a BatchSpanProcessor holds spans until shutdown.
exp2 = InMemorySpanExporter()
p2 = TracerProvider()
p2.add_span_processor(BatchSpanProcessor(exp2, schedule_delay_millis=60_000))
with p2.get_tracer("t").start_as_current_span("x"):
    pass
before = len(exp2.get_finished_spans())
p2.shutdown()
after = len(exp2.get_finished_spans())
flushed = before == 0 and after == 1
print(f"batch spans before shutdown={before} after={after} flushed={flushed}")
provider.shutdown()

sys.exit(0 if all(required.values()) and flushed else 1)
