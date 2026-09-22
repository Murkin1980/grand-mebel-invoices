<!-- MPE:SCOPE-CHANGE-CONTROL:START -->
## Mandatory first read — MPE Scope & Change Control

Before planning, coding, refactoring, dependency changes, testing strategy, deployment, or checkpoint execution, read:

- `docs/governance/SCOPE-CHANGE-CONTROL.md`

Read it before project-specific source-of-truth documents. Then follow this repository's local rules and the current checkpoint/spec.

The scope policy governs minimal change, reuse, checkpoint boundaries, deep-change, testing, evidence, merge/deploy authority, and stopping conditions.

If a local rule appears to conflict with the scope policy, apply the documented source-of-truth priority. Do not silently weaken either rule; surface a deep-change conflict when required.
<!-- MPE:SCOPE-CHANGE-CONTROL:END -->

# Agent Rules

Before any new project, major feature, integration, infrastructure, or architecture change, read and apply `skills/simplicity-first/SKILL.md`.

Create or update `SIMPLICITY_REVIEW.md` before PRDs, architecture, schemas, file trees, implementation phases, Codex instructions, deployment plans, new services, or repositories.

Prefer deletion, consolidation, disabling, and reuse before adding components. Complexity requires measured load, a real failure, a legal requirement, or confirmed user demand.
