#!/usr/bin/env bash
# Risk 1 (opencode-harness): can a project plugin under .opencode/ put text into a
# session's context, and how is it loaded? Reads the OpenCode source (read only)
# and prints each line the answer rests on. Exits 0 only when every check holds.
set -u
SRC=${1:?usage: $0 OPENCODE_SRC}
cd "$SRC" || exit 2
echo "opencode source: $(git log -1 --format='%H %ci' 2>/dev/null)"
fail=0
check() { # label file pattern
  local out
  out=$(grep -nE -- "$3" "$2") || { echo "MISSING [$1] $2 /$3/"; fail=1; return; }
  echo "== $1"; echo "$out" | sed "s|^|$2:|"
}
P=packages
check "plugin folders are plugin/ and plugins/" $P/core/src/plugin/source-directory.ts 'names = \["plugin", "plugins"\]'
check "only .ts/.js files (or directories) load" $P/core/src/plugin/source-directory.ts 'endsWith\("\.ts"\) \|\| entry\.target\.endsWith\("\.js"\)|entry.type === "directory"'
check "project walk looks for .opencode dirs" $P/core/src/config/discovery.ts '"\.opencode", \.\.\.names|path\.basename\(item\) === "\.opencode"'
check "each present .opencode dir becomes a Directory entry" $P/core/src/config.ts 'new Directory\(\{ type: "directory", path: directory \}\)|sources\.project\.filter\(\(root\) => root\.present\)'
check "Directory entries are scanned for plugins" $P/core/src/config/plugin/source.ts 'PluginSourceDirectory\.discover\(fs, entry\.path\)'
check "module shape: default export {id, setup} (or {id, effect})" $P/core/src/plugin/module.ts 'default: Schema\.Union|id: Schema\.String|setup: Schema\.declare|must export a default definition'
check "setup gets ctx; may return cleanup" $P/plugin/src/promise/plugin.ts 'readonly setup: \(context: Context\)|readonly session: SessionDomain|readonly event: EventDomain|readonly location: Location\.Info'
check "session hook 'context' exposes a mutable system prompt" $P/plugin/src/promise/session.ts 'system: Array<SystemPart>|readonly context: SessionContext|readonly hook: ModelHooks<SessionHooks>|"synthetic"'
check "SystemPart is {type:'text', text}" $P/ai/src/schema/messages.ts 'type: Schema\.Literal\("text"\)|text: Schema\.String,'
check "'context' fires before every primary model request" $P/core/src/session/model-request.ts 'primary: \(input\) => prepare\("primary", input, agentHook\("context"'
check "built-in plugin adds a system part in 'context'" $P/core/src/plugin/identity.ts 'event\.system\.splice|session\.hook\("context"'
check "alternative: session.created event + session.synthetic message" $P/core/src/plugin/plan.ts 'session\.created|\.synthetic\(\{'
check "promise hook rejection is not caught (Effect.promise = defect)" $P/plugin/src/promise/adapter.ts 'host\.session\.hook\(name, \(event\) => Effect\.promise'
check "setup rejection is not caught either" $P/plugin/src/promise/adapter.ts 'Effect\.promise\(\(\) => Promise\.resolve\(plugin\.setup\(context2\)\)\)'
check "plugins run in-process under Bun (node builtins importable)" $P/plugin/src/source.bun.ts 'Bun\.Transpiler|Bun\.resolveSync\(item\.path'
exit $fail
