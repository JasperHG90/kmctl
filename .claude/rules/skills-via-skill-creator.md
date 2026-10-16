---
paths: ["apm/.apm/skills/**"]
---

# Skills are made with skill-creator

<constraint name="skills-via-skill-creator">
WHY: a skill whose description never matches what users ask does nothing,
and reading a SKILL.md once does not show that.

Create or change a skill under `apm/.apm/skills/` only through the
skill-creator skill (`anthropic-skills:skill-creator`): draft it, run it on
realistic prompts, and tune its description for triggering. Keep the test
prompts beside the skill so a reviewer can rerun them (ADR 0007).
</constraint>
