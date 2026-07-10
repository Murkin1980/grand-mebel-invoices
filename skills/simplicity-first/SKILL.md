---
name: simplicity-first
description: Mandatory planning filter for keeping MVPs simple.
---
# Simplicity First

Build the smallest system that safely proves the business result.

Before coding:
1. Define the user, exact result, measurable proof, non-goals, and manual fallback without choosing technology.
2. Research three approaches: manual/semi-manual, simplest existing-tool option, and a more automated comparison.
3. Simplify repeatedly: remove nonessential scope, combine components, remove dependencies, and test operational simplicity.
4. Prefer one repository, one application, one database, zero or one worker, zero or one queue, one deployment target, and one provider per function.
5. Score the plan for clarity, few services, few dependencies, easy start, rollback, manual fallback, no speculative scope, one-developer understandability, and end-to-end testability. Proceed only at 16/20 or higher.

Create `SIMPLICITY_REVIEW.md` before PRDs, architecture, schemas, file trees, deployment plans, or Codex instructions. Document the business result, researched options, simplification passes, final workflow, components kept/postponed/rejected, score, risks, manual fallback, and evidence required before adding complexity.
