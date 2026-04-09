# 20260325-multi-agent-workflow-templates

*Source: Business Wiki / prompts/20260325-multi-agent-workflow-templates.html*

## Overview

Modular building blocks for complex, multi-agent coding tasks in Claude Code. These templates leverage **Agent Teams** (`TeamCreate`) with inter-agent messaging, shared task lists, QA feedback loops, and plan approval gates.

Use individually or chain together depending on the task:

| Combo | When |
|-------|------|
| 1 only | Pure research / investigation |
| 1 &rarr; 2 | Research + plan doc (hand off to human or future session) |
| 3 &rarr; 4 | Implementation + validation (plan already exists) |
| 1 &rarr; 2 &rarr; 3 &rarr; 4 | Full lifecycle for complex features or critical bug fixes |
| 3 only | Quick multi-agent implementation (small scope, plan is obvious) |

Replace `[bracketed]` placeholders with your specifics. The orchestrator has freedom to adjust team size, roles, and approach based on what it discovers.

---

## Phase 1 &mdash; Research

```
[Describe the problem or feature request in detail. Include context,
acceptance criteria, and any relevant Asana task links.]

PHASE 1 &mdash; RESEARCH:

GOAL: Thoroughly understand [the problem / topic / how to achieve X].
I need a clear, complete picture before any code changes happen.

Create an agent team of 2-4 teammates using Sonnet (you decide the
exact count based on complexity). Suggested roles &mdash; adapt as needed:

1. Deep Investigator &mdash; Dive into the codebase and trace the relevant
   code paths end-to-end. Read every file that touches [area]. Map data
   flow, dependencies, and edge cases. Document exactly what exists
   today and where the issues are.

2. Architect Analyst &mdash; Look at this from the system-wide perspective.
   Read CLAUDE.md, the project architecture docs, and understand how
   [area] connects to other components. Identify what else could be
   affected. Think about: What breaks if we change X? What are the
   second-order effects? Which connected systems need attention?

3. External Researcher (if needed) &mdash; Research [external topic / best
   practices / library docs / API documentation]. Use web search and
   documentation tools. Focus on practical, proven approaches &mdash; not
   theoretical.

Each teammate: Take your time. Be thorough over fast. Read full files,
not just grep results. When you find something important, message your
teammates immediately so they can factor it into their own investigation.

DELIVERABLES:
- Each teammate sends their findings to the Architect Analyst
- The Architect Analyst produces a consolidated research summary
  covering: (a) current state, (b) root cause or full picture,
  (c) affected areas and risks, (d) recommended approach with trade-offs
- Save the final summary as a structured document I can review

COORDINATION: Teammates should actively message each other when they
discover something that affects another's investigation. The Architect
Analyst should challenge findings &mdash; ask "what about X?" and "did you
check Y?" before finalizing.
```

---

## Phase 2 &mdash; Plan

```
PHASE 2 &mdash; PLAN:

Based on the research [just completed / in document X], write a phased
implementation plan.

This is a production codebase &mdash; not an MVP. I need:
- Professional, robust architecture over quick fixes
- Future-proof design that doesn't create technical debt
- Every phase small enough to be independently verifiable
- Enough context that any senior engineer (human or LLM) can execute
  each phase without ambiguity

Create the plan as a new hardprompt document at
[path, e.g. docs/dev-specs/YYYYMMDD_FEATURE_NAME.md].

STRUCTURE for each phase:
1. Goal (one sentence)
2. Files to create/modify (with specific line ranges or functions
   when modifying)
3. What changes and why
4. Safety invariants &mdash; what must NOT break
5. How to verify this phase worked (test command, manual check,
   or assertion)

ALSO INCLUDE:
- Downstream Impact Analysis &mdash; table of every consumer of the
  changed code and whether it needs updates
- Risk areas &mdash; explicitly call out the #1 and #2 things most
  likely to go wrong
- Rollback approach &mdash; how to undo if something breaks
- Files NOT to touch &mdash; prevent scope creep

Take your time. This plan is the blueprint &mdash; getting it right prevents
costly rework during implementation. Review it against the full codebase
before finalizing.
```

---

## Phase 3 &mdash; Implement

```
PHASE 3 &mdash; IMPLEMENT:

GOAL: Implement [feature / fix / the plan at docs/dev-specs/XXXX.md].

This is a production codebase beyond MVP. Sloppy changes break working
systems. Quality and system integrity are non-negotiable.

Create an agent team. You decide the team size (2-5) and exact roles
based on what this task needs. Here is the minimum structure &mdash; add
specialists as needed:

REQUIRED ROLES:

1. Implementer(s) &mdash; Write the code. Each implementer owns specific
   files (no overlapping file edits between teammates). Follow the
   phased plan if one exists. When a phase is done, message the
   Architect before moving to the next phase.

2. Architect Overseer &mdash; Does NOT write implementation code. This
   agent's job is system integrity:
   - Read every file the implementers modify, end-to-end
   - Trace how changes propagate through the system &mdash; check connected
     components, API consumers, downstream stages, UI pages, types,
     imports
   - Proactively grep the codebase for other references to modified
     functions, types, constants, or patterns
   - When an implementer finishes a phase, review it and either approve
     or send it back with specific issues
   - Think about: What did we forget? What else uses this? What breaks
     in edge cases (top-up, re-run, translation, empty states)?

OPTIONAL ROLES (orchestrator decides):

3. QA Agent &mdash; Reviews code quality, catches bugs, tests edge cases.
   When issues are found, message the specific implementer with exact
   file:line and what's wrong. The implementer fixes and messages back.
   QA re-reviews. This loop continues until QA passes.

4. Integration Specialist &mdash; For cross-cutting changes: verify API
   contracts, database schema compatibility, type consistency across
   boundaries, prompt template updates, etc.

RULES FOR ALL TEAMMATES:
- Take your time and work thoroughly. Read full files before editing.
  Understand before changing.
- Never assume &mdash; verify by reading the actual code
- If you discover something that affects another teammate's work,
  message them immediately
- If unsure about an approach, message the Architect Overseer for
  guidance before proceeding
- Save intermediate work frequently

COORDINATION:
- The Architect Overseer is the quality gate. No phase is "done" until
  the Architect approves it.
- QA issues get sent directly to the responsible implementer (not
  through the orchestrator)
- If the QA agent finds critical issues, those implementers must
  address them before new work starts
- The orchestrator should wait for all teammates to finish and confirm
  before proceeding

DELIVERABLE: Working implementation with the Architect's confirmation
that system integrity is maintained.
```

---

## Phase 4 &mdash; Validate

```
PHASE 4 &mdash; VALIDATE:

GOAL: Validate the implementation [just completed / of feature X]. This
is the final quality gate before we ship. Nothing gets merged with
unverified assumptions.

Create an agent team of 2-3 teammates:

1. Architect Validator &mdash; Full system integrity review:
   - Mentally trace execution through the entire modified pipeline/flow
     end-to-end
   - For every modified file: read it completely, verify it's consistent
     with its callers and callees
   - Check for: broken imports, type mismatches, missing error handling
     at boundaries, functions that changed signature but have callers
     not yet updated
   - Verify downstream consumers: does [the UI / API / pipeline stage /
     KB generation / etc.] still work correctly with the changes?
   - Check edge cases: empty states, error paths, concurrent operations
     (top-up while running, re-run, translation)
   - Produce a pass/fail verdict with specific file:line references for
     any issues

2. Code Quality Reviewer &mdash; Line-by-line review of every changed file:
   - Look for bugs, off-by-one errors, null/undefined risks, race
     conditions
   - Verify error handling is adequate (not excessive &mdash; just adequate)
   - Check that no debug code, console.logs, or temporary hacks were
     left in
   - Verify naming consistency and that new code follows existing
     patterns in the codebase
   - Check for security issues (SQL injection, unvalidated input at
     boundaries, exposed secrets)

3. Regression Checker (optional, orchestrator decides based on scope):
   - Run the test suite and report results
   - Grep for TODO/FIXME/HACK that were added during implementation
   - Verify that files listed as "not to touch" in the plan were indeed
     not touched
   - Check git diff for any unintended changes (files modified that
     shouldn't have been)

RULES FOR ALL TEAMMATES:
- Take your time. Thoroughness over speed. This is the last line of
  defense.
- Read the actual code &mdash; don't rely on assumptions about what was
  implemented
- If you find an issue, message the other validators to check if it
  affects their review area
- Don't just check that new code works &mdash; verify that existing
  functionality wasn't broken

DELIVERABLE: Each validator produces a structured verdict:
- PASS with confidence notes, or
- FAIL with specific issues (file:line, description, severity)

If ANY validator fails, the issues must be fixed and this validation
round re-run. Do not merge or mark as complete with open issues.
```

---

## Full Lifecycle Example

For maximum quality on complex tasks, chain all four phases:

```
[Describe the problem or feature request in detail. Include context,
acceptance criteria, and any relevant Asana task links.]

PHASE 1 &mdash; RESEARCH:
[Paste Template 1 with specifics filled in]

PHASE 2 &mdash; PLAN:
Now write a phased implementation plan based on the research.
Save to docs/dev-specs/YYYYMMDD_FEATURE_NAME.md.
Follow the standard plan template structure.

PHASE 3 &mdash; IMPLEMENT:
Now implement the plan using a multi-agent team with architect oversight.

PHASE 4 &mdash; VALIDATE:
Now do a multi-agent validation round.

AFTER VALIDATION PASSES:
[Optional: Update the PR, merge, update Asana, notify team &mdash; whatever
your workflow needs]
```

When chaining in a single session, phases 2-4 can be shortened since the context carries forward from earlier phases.

---

## Tips &amp; Best Practices

**Cost:** Agent teams run ~3-5x the tokens of a solo session. Use them for the ~50% of tasks that are complex enough to warrant it.

**Visibility:** With `teammateMode: "tmux"` enabled, run from terminal (not VS Code extension) to see all agents in split panes.

**Model mixing:** For cost optimization, consider Sonnet for implementers and Opus for the Architect Overseer on critical tasks.

**Key principles:**
- Each agent owns specific files &mdash; no overlapping edits between teammates
- 3-5 teammates is the sweet spot (token costs scale linearly per agent)
- 5-6 tasks per teammate is ideal granularity
- Teammates don't inherit conversation history &mdash; give them complete context in spawn prompts
- Explicitly tell the lead to "wait for teammates to finish" (it sometimes starts implementing itself)
- Start with read-only tasks (research, investigation) before parallel writing

**When NOT to use agent teams:**
- Sequential tasks where each step depends on the previous
- Same-file edits (agents may overwrite each other)
- Simple tasks that a single session handles fine
- When you need everything in one context window
