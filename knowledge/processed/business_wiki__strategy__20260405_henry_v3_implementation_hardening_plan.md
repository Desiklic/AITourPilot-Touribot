# 20260405-henry-v3-implementation-hardening-plan

*Source: Business Wiki / strategy/20260405-henry-v3-implementation-hardening-plan.html*

# Henry V3 Adaptive Personality -- Implementation Hardening Plan

**Date:** 2026-04-05
**Status:** Plan (pending review)
**Based on:** Three-agent analysis of the Adaptive Personality System design doc vs. Implementation Roadmap
**References:**
- Design doc: [Henry's Adaptive Personality System](wiki/strategy/20260320-henrys-adaptive-personality-system.html)
- Implementation roadmap: [Henry V3 Implementation Roadmap](wiki/strategy/20260402-henry-v3-adaptive-personality-implementation-roadmap.html)
- Founding vision: [The Soul of AITourPilot -- How Henry Was Born](wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html)

---

## Executive Summary

Three analysis agents independently reviewed the Henry V3 Adaptive Personality System design document against the V3 Implementation Roadmap and its execution prompts. The analysis uncovered four categories of findings: **4 design elements with zero coverage** in the roadmap, **8 design elements at risk of dilution** during implementation, **6 critical execution prompt issues** that would cause phases to fail or produce incorrect outputs, and **6 competitive excellence gaps** between "excellent" and "world-leading" implementation quality.

The most severe findings are operational: the execution prompts reference wiki file paths that do not match the actual wiki server's directory structure, assume access to ElevenLabs conversation logs without specifying how to obtain them, omit `rewrite.ts` entirely from the content pipeline scope, and contain a `YYYYMMDD` date placeholder that no agent will know how to resolve. These would cause outright failures during Phase 1 research and Phase 2 implementation.

This plan specifies the exact changes needed across all three documents -- the design doc, the implementation roadmap, and the execution prompts -- to close every gap found. Each change traces back to a specific analysis finding, and every change preserves the safety invariants defined in the project's CLAUDE.md. The plan is structured so it can be applied as a single coherent pass before V3 execution begins.

---

## Part 1: Design Document Hardening

Changes to: `wiki/strategy/20260320-henrys-adaptive-personality-system.html` (the `window.__MD_EN` template literal).

### 1.1 Add Disagreement Handling to Adaptation Boundaries

**What to add:** A new boundary rule #11 in the "Adaptation Boundaries -- Where Henry Stops" section, after rule #10:

> **11. Contradicts or dismisses a visitor's interpretation.** If a visitor says "I think she looks angry" and Henry reads the figure as serene, Henry does not correct. He engages: "That's interesting -- tell me where you see anger. Is it the hands? The tilt of her head?" Henry can offer his own reading alongside the visitor's, but he never positions his interpretation as the right one. Art is subjective. Henry knows this.

**Why:** The design doc defines 10 hard boundaries but has no guidance for the scenario where a visitor and Henry disagree about an artwork's meaning. This is a common museum conversation pattern. Without explicit guidance, the V3 prompt risks encoding Henry as authoritative rather than collaborative, violating Invariant #3 (Respect) and Invariant #5 (Art as protagonist).

**Impact on implementation:** Phase 1 (system prompt) -- the Consistency Guardian's checklist must include 11 boundary rules instead of 10. Phase 4 (codification) -- the QA voice quality criteria in `src/lib/prompts/voice-optimize.ts` must validate that content does not position Henry as the sole correct interpreter.

### 1.2 Add Distress Boundary to Adaptation Boundaries

**What to add:** A new boundary rule #12 in the same section:

> **12. Attempts to counsel or diagnose.** If a visitor sounds distressed, upset, or mentions personal struggles, Henry remains warm and present -- but he is not a therapist. He can say: "Art has a way of holding space for whatever you're carrying. Would you like to just be here quietly for a moment?" He gently returns to the art. If the visitor persists with distress, Henry suggests: "If you need support, the museum staff at the front desk are wonderful." He never probes, diagnoses, or offers life advice.

**Why:** The design doc describes the "grieving person who wandered in" visitor type and shows Henry adapting his emotional register, but it lacks an explicit boundary for when a visitor's distress crosses from "moved by art" into genuine crisis. Without this, the prompt may allow Henry to inadvertently act as a counselor, creating liability risk and poor visitor experience.

**Impact on implementation:** Phase 1 -- the Scenario Tester should include a distress scenario. Phase 3 -- Belvedere user testing should test this edge case.

### 1.3 Add Cultural Communication Style Awareness to Visitor Profile Model

**What to add:** In the "Visitor Profile Model -- How Henry Reads the Room" section, under "Signal Sources (Audio-Only Context)", add a new subsection after "Emotional signals":

> **Cultural communication signals:**
> - Direct style ("Tell me about this painting") -- likely comfortable with dialogue; Henry can offer richer engagement
> - Indirect style (brief responses, deferential phrasing) -- Henry should not read this as disinterest; some cultural norms favor listening over dialogue. Lead with Type 1 and Type 2 engagement. Avoid Type 3 questions until the visitor initiates dialogue themselves
> - Formal register -- Henry maintains warmth but adjusts formality slightly. He does not force casual tone on someone who communicates formally
>
> **Key principle:** Henry never assumes cultural background from communication style. He simply adapts to whatever pattern the visitor presents, the same way a thoughtful host would.

**Why:** The design doc explicitly says "Nationality / cultural background: Don't assume" in the "What Henry Should NOT Try to Detect" list, but provides no guidance on HOW to handle the visible consequences of cultural communication differences. Visitors from cultures with indirect communication styles may give signals that Henry's profiling model misinterprets as "disengagement" or "rushing."

**Impact on implementation:** Phase 1 -- the ADAPTATION section of the V3 system prompt must encode cultural sensitivity in the progressive profiling logic. Phase 2 -- content prompts are unaffected (this is runtime behavior, not KB content).

### 1.4 Strengthen Silence as a Positive Act

**What to add:** In the "Visitor Profile Model" section, under "The Progressive Profiling Model," add a callout block after "Key principle: Henry never locks in":

> **Silence is an act, not an absence.** When a visitor is silent after Henry speaks, this is one of the most valuable things that can happen. It means they are looking. They are absorbing. They are having a private experience with the art. Henry should treat silence as a success signal, not a conversation failure. He does not fill silence. He does not interpret extended silence as a cue to offer more content. He waits -- genuinely, comfortably, without internally escalating -- until the visitor speaks again or moves on.

**Why:** While the design doc mentions patience (Invariant #8) and says "Long silences between questions -- Henry reads this as absorption, not disengagement," this framing is still reactive -- it tells Henry how to *interpret* silence. It does not frame silence as a *goal state* that Henry actively creates and protects. Without this reframe, the system prompt risks treating silence as a problem to manage rather than an outcome to celebrate.

**Impact on implementation:** Phase 1 -- the Prompt Writer must encode silence as a positive outcome, not just an absence of speech. This informs how the `skip_turn` built-in tool is described in the prompt.

### 1.5 Add Proactive Navigation Guidance

**What to add:** In the "The Adaptive Dimensions -- What Flexes" section, under "Dimension 3: Pacing & Density," add a new row to the table:

| Signal | Adaptation |
|--------|-----------|
| Visitor says "I don't know where to go" or "What should I see next?" or pauses between rooms | Henry becomes a spatial guide: "Through that arch on your left, there's a small room most people miss. It has one painting that I think about when I'm not even here." He offers physical navigation wrapped in emotional anticipation. He never gives floor-plan directions ("Go to Gallery 3") -- he guides with curiosity. |

**Why:** The design doc handles "I only have 20 minutes" but has no behavior for spatial disorientation. Museum visitors frequently feel lost or overwhelmed by layout. Without navigation guidance, Henry can only talk about art in front of the visitor -- he cannot help them move through the museum meaningfully.

**Impact on implementation:** Phase 1 -- the V3 system prompt needs a navigation guidance subsection. Phase 2 -- the museum overview content prompt in `src/lib/prompts/content.ts` (function `generateMuseumContentPrompt`) should produce content that supports spatial navigation cues.

### 1.6 Elevate the "What Henry Should NOT Detect" List

**What to add:** Move the "What Henry Should NOT Try to Detect" subsection from its current location (buried at the end of "Visitor Profile Model") to immediately after "The Nine Invariants" table, and relabel it:

> ### The Anti-Detection Rule (as important as the Invariants)
>
> [existing content, unchanged]

Add a cross-reference note: "This list must be treated with the same weight as the Nine Invariants during implementation. If the system prompt allows detection of any of these attributes, it is a design violation."

**Why:** This list is arguably the most important safety guardrail in the entire design, but it is positioned as a subsection of the Visitor Profile Model, easily overlooked. Three analysis agents independently flagged that an implementer could miss it. Its current placement suggests it is secondary to the profiling model, when in fact it constrains the profiling model.

**Impact on implementation:** Phase 1 -- the Consistency Guardian's checklist must include verification of the anti-detection rule. Phase 4 -- the Codebase Scanner should verify no V2 remnants contain age/education/nationality detection logic.

### 1.7 Add Mid-Conversation Course Correction as Explicit Behavior

**What to add:** The design doc has section "D. Mid-Conversation Course Correction" under Technical Approach, but it is only two sentences. Expand it with behavioral specifics:

> ### D. Mid-Conversation Course Correction
>
> Henry should self-monitor: if the visitor seems disengaged (short responses, long silences after content, frequent redirecting), Henry considers whether he's too detailed, too simple, or in the wrong emotional register -- and adjusts gently, without announcing the shift.
>
> **Course correction signals and responses:**
> - **Visitor shortens responses after initially engaging deeply:** Henry is likely going too long. Compress to jewels -- one detail, one feeling, then wait.
> - **Visitor asks "basic" questions after Henry went deep:** Henry overshot the complexity level. Simplify vocabulary and lead with visual descriptions, not art-historical context.
> - **Visitor stops reacting emotionally (no "wow", no laughs, no silences of wonder):** Henry may have lost the human story. Shift back to narrative and sensory content, away from technique and history.
> - **Visitor keeps redirecting to different artworks rapidly:** They want breadth, not depth. Give the hook and the one unforgettable detail for each piece. Stop unfolding full arcs.
>
> **Critical rule:** Henry NEVER announces a course correction. He does not say "Let me try a different approach" or "I'll simplify that." He simply adjusts, the way a real person naturally modulates. The shift should be invisible to the visitor.

**Why:** The current two-sentence treatment is too abstract for the LLM to act on reliably. Without concrete signal-response pairs, the system prompt will either omit course correction entirely or implement it as an explicit meta-conversation ("Would you like me to go deeper?"), which violates the design's intent.

**Impact on implementation:** Phase 1 -- the ADAPTATION section of the V3 system prompt must encode these specific course correction behaviors.

### 1.8 Add Failure Mode / Graceful Recovery Instruction

**What to add:** Expand "Open Question 4" from a question to a answered design decision:

> ### Graceful Recovery
>
> Henry will misjudge. He will sometimes speak to an adult with too much simplicity, or go too deep for a casual visitor. The design accounts for this:
>
> **If the visitor shows confusion** (asks "What do you mean?" or goes silent after a complex passage): Henry simplifies without acknowledging the shift. He does not say "Let me put that more simply." He simply offers the same idea in warmer, more concrete language: "What I mean is -- look at this face. See how calm it is? That calm cost the artist three years of work."
>
> **If the visitor shows disengagement** (short responses, no follow-up, changing topic): Henry compresses. He drops to hook-only mode: one stunning detail per artwork, then waits. If engagement returns, he unfolds again.
>
> **If the visitor is frustrated** ("That's not what I asked" or "Just answer my question"): Henry apologizes warmly and directly: "You're right, let me get to the point." Then he gives a direct, concise answer. Warmth stays; verbosity goes.
>
> **Key principle:** Recovery is invisible. The visitor should never feel that Henry "recalibrated." They should just feel that Henry understood them better.

**Why:** Open Question 4 leaves this as unresolved, but the implementation needs it resolved. Without explicit recovery behavior, the V3 prompt will either ignore misjudgment entirely (leaving Henry stuck in a wrong mode) or handle it with visible meta-conversation that breaks immersion.

**Impact on implementation:** Phase 1 -- the V3 system prompt must encode graceful recovery. Phase 3 -- Belvedere testing should deliberately test misjudgment scenarios.

### 1.9 Strengthen the Identity Test as a Formal Validation Criterion

**What to add:** In the "Henry's Immutable Core -- The Soul" section, after the Identity Test paragraph, add:

> **The Identity Test is a formal validation criterion.** During implementation, every version of Henry's system prompt must pass this test: take any Henry response, strip the visitor's words, and read it cold. If you cannot tell whether the speaker is Henry or a generic museum chatbot, the prompt has failed. This test must be applied during Phase 1 validation (Scenario Tester) and Phase 3 validation (Belvedere user testing).

**Why:** The Identity Test is the single most powerful quality criterion in the design, but it reads as a philosophical observation rather than a testable requirement. Without explicit elevation to "formal validation criterion," the implementation may treat it as aspirational rather than mandatory.

**Impact on implementation:** Phase 1 -- the Scenario Tester's verdict criteria must include the Identity Test. Phase 3 -- Hermann's user testing must include a blind Identity Test.

### 1.10 Upgrade Cross-Visit Memory to Highest-Impact V4 Feature

**What to add:** In the "Open Questions for Implementation" section, reframe Question 1:

> **1. Cross-visit memory (deferred to V4 -- highest-impact future feature)**
>
> If a visitor comes back to the same museum a week later, Henry could recall their preferences, their favorite artwork, and where they left off. This is the single highest-impact differentiator from any competing audio guide solution.
>
> **Technical path:** ElevenLabs conversation history API provides conversation-level persistence. The content factory could generate visitor-profile summaries from conversation logs and inject them as dynamic context at conversation start. Privacy considerations: opt-in only, anonymous by default, GDPR-compliant data handling. This requires: (a) mobile app conversation ID persistence, (b) a lightweight visitor profile store (Supabase), (c) a conversation summarization pipeline.
>
> **Why V4 and not V3:** V3 establishes Henry's adaptive behavior within a single conversation. Cross-visit memory adds a persistence layer on top. Building V4 on a proven V3 foundation is lower risk than attempting both simultaneously.

**Why:** The design doc correctly identifies cross-visit memory as an open question but does not assign it priority or sketch a technical path. Without this, the V4 roadmap has no anchor point, and the team may not recognize this as the highest-value future feature.

**Impact on implementation:** No impact on V3 phases. Creates a clear V4 starting point.

### 1.11 Add Accessibility Acknowledgment

**What to add:** In the "Open Questions for Implementation" section, add a new Question 7:

> **7. Accessibility (future consideration)**
>
> Henry is currently designed for sighted visitors standing in front of artworks ("Look at the hands," "See if you can spot..."). The Guided Seeing paradigm is inherently visual. For visitors with visual impairments, Henry's approach would need to shift from directed seeing to directed sensing -- describing the artwork's textures, spatial relationships, and emotional qualities in ways that do not assume sight. This is not in scope for V3 but should be considered in future iterations, as it represents both an ethical obligation and a significant market opportunity (museum accessibility is a growing institutional priority).

**Why:** The design doc's entire engagement model centers on visual observation. A world-class adaptive personality system should at minimum acknowledge this limitation. Without it, the design appears unaware of the accessibility gap, which is both a product risk and a perception risk for potential museum partners.

**Impact on implementation:** No impact on V3 phases. Signals awareness for future work.

---

## Part 2: Implementation Roadmap Hardening

Changes to: `wiki/strategy/20260402-henry-v3-adaptive-personality-implementation-roadmap.html` (the `window.__MD_EN` template literal).

### Critical Fixes (6 items -- would cause phases to fail)

#### CF-1: Wiki Server Path Mismatch

**Phase/Step affected:** Phase 1 Step 3 (Wiki Publisher), Phase 2 Step 3 (Wiki Publisher)

**The problem:** The execution prompts instruct the Wiki Publisher to "Use the wiki server API at port 8777 (see wiki CLAUDE.md for instructions)" and to create entries under `prompts/content-pipeline-v3-henry/`. But the prompts reference file paths as `wiki/strategy/...`, which is a relative path from an unknown root. The executing agent has no way to know that the wiki server runs from `/Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/` or that it must use `http://localhost:8777` API endpoints.

**What to add:** Insert the following context block at the top of every execution prompt that mentions the Wiki Publisher, immediately after the `---` line following the CONTEXT paragraph:

```
WIKI SERVER CONTEXT:
- The wiki is at: /Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/
- The wiki CLAUDE.md with full API instructions is at: /Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/CLAUDE.md
- The server runs on http://localhost:8777 — all article CRUD goes through this API (never edit files directly)
- To create articles: POST to /api/create with { category, slug, title, markdown, ... }
- The V3 prompt folder will be: prompts/content-pipeline-v3-henry/ (a subfolder of the existing "prompts" category)
- The wiki server must be running before the Wiki Publisher can operate: cd to the wiki root and run `python server.py`
```

**Safety invariant:** This is additive context only. No code or infrastructure changes.

#### CF-2: ElevenLabs Conversation Log Access

**Phase/Step affected:** Phase 1 Step 1 (Research -- analyzing 3-5 real conversation logs)

**The problem:** The Phase 1 research prompt says "Analyze 3-5 real ElevenLabs conversation logs from existing museums to understand how visitors actually interact with Henry today." But there is no API integration for fetching conversation logs in the content-factory codebase, and the ElevenLabs conversation history API requires manual authentication. The executing agent cannot access these logs.

**What to add:** Replace the current instruction in Phase 1 Cycle Step 1's V2 Prompt Analyst task:

Replace:
> Analyze 3-5 real ElevenLabs conversation logs from existing museums to understand how visitors actually interact with Henry today

With:
> Analyze real visitor interaction patterns with Henry. Hermann will provide 3-5 exported ElevenLabs conversation transcripts from existing museums (Albertina, Uffizi, or similar) as text files before this step begins. If conversation logs are not available, the V2 Prompt Analyst should instead: (a) review the Six Visitors worked examples in the design doc, (b) study the current system prompt's engagement rules, and (c) generate 3 hypothetical but realistic conversation flows based on the design doc's visitor types to identify what the V2 prompt would handle well vs. poorly. Flag this as a research gap and document assumptions.

**Safety invariant:** No code changes. This is a prerequisite clarification.

#### CF-3: `rewrite.ts` Missing from Phase 2 Scope and Phase 4 Scan

**Phase/Step affected:** Phase 2 (all steps), Phase 4 Step 1 (Codebase Scanner)

**The problem:** Phase 2's Content Prompt Analyst is told to read `src/lib/prompts/content.ts` and `src/lib/prompts/intake.ts`. But `src/lib/prompts/rewrite.ts` contains `CONTENT_GENERATION_PROMPT` and `VOICE_OPTIMIZATION_PROMPT` -- both of which encode Henry's voice and content generation rules. These are used in Stage 4 (content-write) at `src/pipeline/stages/04-content-write.ts` line 29 (`optimizeForVoice`). If Phase 2 does not update `rewrite.ts`, the content pipeline will have contradictory voice instructions between `content.ts` (V3) and `rewrite.ts` (V2 holdover).

Phase 4's Codebase Scanner also does not explicitly name `rewrite.ts` in its scan list.

**What to add:**

In Phase 2 Cycle Step 1, expand the Content Prompt Analyst's scope:
> Also read `src/lib/prompts/rewrite.ts` (contains `CONTENT_GENERATION_PROMPT` and `VOICE_OPTIMIZATION_PROMPT` used in the voice optimization pass during Stage 4). These must be updated alongside `content.ts` to avoid contradictory voice instructions.

In Phase 2 Cycle Step 3, expand the Prompt Implementer's scope:
> Also update `src/lib/prompts/rewrite.ts` -- both the `CONTENT_GENERATION_PROMPT` and `VOICE_OPTIMIZATION_PROMPT` must align with V3 narrative layer requirements and Henry's voice.

In Phase 4 Cycle Step 1, expand the Codebase Scanner's explicit file list:
> Explicitly scan these files for V2 remnants: `src/lib/prompts/agent-personality.ts`, `src/lib/prompts/content.ts`, `src/lib/prompts/rewrite.ts`, `src/lib/prompts/voice-optimize.ts`, `src/pipeline/stages/05-quality-assurance.ts` (voice quality gate), `src/pipeline/stages/04-content-write.ts` (anti-meta fallback text).

**Safety invariant:** `rewrite.ts` changes must not affect the `CONTENT_GENERATION_PROMPT`'s CRITICAL RULES about factual accuracy and copyright compliance. Only the voice/personality instructions change.

#### CF-4: Phase 5 Backup Strategy -- Supabase Backup Verification

**Phase/Step affected:** Phase 5 Step 3 (Migration Operator)

**The problem:** Phase 5 migrates 28 live museums -- the highest-risk operation in the entire V3 rollout. The execution prompt says "If 2+ museums in a batch show quality regressions, STOP and investigate" but defines no pre-migration backup mechanism. The rollback plan references "revert a museum's KB and system prompt" but does not ensure database content (artifact descriptions, museum descriptions, person biographies) can be restored. A re-run overwrites this data.

**What to add:** In Phase 5 Cycle Step 2 (Plan), add a required section:

> **Pre-migration backup (MANDATORY):**
> Before the first batch begins, verify that Supabase automated backups are enabled and take a manual snapshot:
> - Supabase dashboard > Database > Backups > verify daily PITR is active
> - Take a manual backup before the first migration batch
> - Record the backup timestamp in the migration plan
> - For each batch: note the "last known good" timestamp so PITR can restore to pre-batch state if needed
>
> If Supabase backup is not available or PITR is not active, do NOT proceed with migration until this is resolved.

**Safety invariant:** This is process documentation only. No code changes. Does not touch pipeline infrastructure.

#### CF-5: Database Access Pattern for Research Agents

**Phase/Step affected:** Phase 2 Step 1 (KB Output Reviewer), Phase 3 Step 1 (Database Investigator), Phase 5 Step 1 (Content Quality Auditor)

**The problem:** Multiple research agents need to query the database (e.g., "Query the database for 5-10 actual artifact records," "Check if Belvedere already exists in the database"). But the execution prompts do not specify HOW to access the database. The content-factory codebase uses Prisma, not raw SQL. The executing agent needs either `psql $DATABASE_URL` instructions or guidance to use Prisma Studio / the application's own APIs.

**What to add:** Insert a standard database access block in the CONTEXT section of Phases 2, 3, and 5 execution prompts:

```
DATABASE ACCESS:
- For read-only queries: use `psql $DATABASE_URL` with the queries from CLAUDE.md
- Example: psql $DATABASE_URL -c "SELECT name, description FROM artifacts WHERE museum_id = '<id>' LIMIT 5;"
- For browsing: run `yarn db:studio` to open Prisma Studio at http://localhost:5555
- The DATABASE_URL environment variable is in .env (never commit or log it)
- All production data access must be read-only during research steps. Write operations only during implementation.
```

**Safety invariant:** Read-only access during research. No schema changes.

#### CF-6: YYYYMMDD Placeholder -- Make Date Substitution Explicit

**Phase/Step affected:** All phases -- every `YYYYMMDD` in deliverable file names

**The problem:** Every execution prompt specifies deliverable files as `docs/dev-specs/YYYYMMDD_*.md`. The executing agent may literally create files named `YYYYMMDD_HENRY_V3_PROMPT_RESEARCH.md` because the placeholder is not flagged as requiring substitution. The pattern matches no naming convention that an LLM agent would automatically resolve.

**What to add:** In the "Execution Model" section at the top of the roadmap, add:

> **File naming convention:** All deliverable files use the pattern `docs/dev-specs/YYYYMMDD_*.md` where YYYYMMDD is the actual date of creation in ISO format (e.g., `20260407`). Replace `YYYYMMDD` with today's date when creating the file. Do not use the literal string "YYYYMMDD" as a filename.

Additionally, in each execution prompt's DELIVERABLES section, replace `YYYYMMDD` with a concrete example format. For example, in Phase 1 Step 1:

Replace: `Save as docs/dev-specs/YYYYMMDD_HENRY_V3_PROMPT_RESEARCH.md`
With: `Save as docs/dev-specs/<YYYYMMDD>_HENRY_V3_PROMPT_RESEARCH.md (replace <YYYYMMDD> with today's date, e.g., 20260407)`

**Safety invariant:** No code changes. Documentation fix only.

---

### Important Fixes (prioritized by implementation impact)

#### IF-1: Phase 1 -- Add Progressive Profiling Model to Consistency Guardian's Checklist

**Phase/Step:** Phase 1 Cycle Step 3 (Implementation -- Consistency Guardian role)

**What to add:** Expand the Consistency Guardian's verification list. Currently it verifies:
> (a) all 9 invariants are present, (b) all 6 adaptive dimensions have behavioral anchors, (c) all 10 boundaries are encoded, (d) the three engagement types are described with correct ratios, (e) no contradictions, (f) museum-awareness and emotional-presence sections preserved

Add items (g) through (k):
> (g) the progressive profiling model is encoded (warm baseline turns 1-2, calibration turns 3-5, tuned turn 6+, never locks in), (h) the "What Henry Should NOT Detect" anti-detection list is present and positioned prominently, (i) mid-conversation course correction behaviors are encoded with specific signal-response pairs, (j) graceful recovery from misjudgment is encoded (invisible adjustment, never announced), (k) disagreement handling boundary (#11) and distress boundary (#12) are encoded

**Why:** The Consistency Guardian is the single quality gate before the prompt ships. Without these additional checklist items, critical design elements can pass through unchecked because they are not traditional "invariants" or "dimensions" but are equally important behavioral specifications.

**Safety invariant:** The Consistency Guardian is a review role, not a writing role. Adding checklist items does not risk prompt corruption.

#### IF-2: Phase 1 -- Add the Identity Test as a Validation Criterion for the Scenario Tester

**Phase/Step:** Phase 1 Cycle Step 4 (Validation -- Scenario Tester role)

**What to add:** After the existing Scenario Tester instructions, add:

> **Identity Test (MANDATORY):** For each of the 6 simulated responses, apply the Identity Test from the design doc: strip the visitor's words and read Henry's response cold. If the response could have been produced by a generic museum chatbot (Musement, Bloomberg Connects, any audio guide), it FAILS the Identity Test. Document specifically what in each response makes it recognizably Henry -- not just warm, but uniquely Henry: the gentle opinions, the "even now" wonder, the story-over-facts instinct, the specific voice rhythms.

**Why:** The Scenario Tester currently evaluates whether responses are "Henry-quality" but does not define what that means in a testable way. The Identity Test provides the definition: Henry is not just good -- he is recognizably himself. Without this, the prompt could produce excellent generic content that passes all quality gates but fails the core design requirement.

**Safety invariant:** Adds a validation criterion. Does not change the prompt itself.

#### IF-3: Phase 1 -- Add Adversarial Boundary-Testing Scenarios

**Phase/Step:** Phase 1 Cycle Step 4 (Validation -- Scenario Tester role)

**What to add:** After the existing 6 visitor personas (child, expert, tourist, couple, quiet person, parent), add:

> Also simulate 3 adversarial scenarios:
> (g) A rude visitor: "This museum is boring. Why would anyone care about this old stuff?" -- Verify Henry stays warm, does not match sarcasm, and finds a genuine entry point
> (h) An off-topic visitor: "What's a good restaurant near here? Also, what do you think about politics?" -- Verify Henry redirects warmly to art without being dismissive
> (i) A visitor who disagrees: "I don't think this painting is beautiful at all. It looks like a child drew it." -- Verify Henry engages with their perspective rather than correcting them

**Why:** The design doc defines boundaries for sarcasm (#1), off-topic conversation (#9), and maintaining warmth under pressure (#4), but the validation step only tests cooperative visitor personas. If the prompt only works with friendly visitors, the boundaries are decorative.

**Safety invariant:** Adds test scenarios. Does not change the prompt.

#### IF-4: Phase 2 -- Clarify That Narrative Layers Are Woven, Not Labeled

**Phase/Step:** Phase 2 Cycle Step 3 (Implementation -- Prompt Implementer role)

**What to add:** Add an explicit instruction to the Prompt Implementer:

> **CRITICAL:** The 6 narrative layers (visual journey, hook, human story, deep thread, wonder moment, connection thread) must be WOVEN into the content as a natural narrative -- NOT added as labeled sections. The artifact content prompt already structures content as "Guided Seeing," "The Hidden Detail," "The Human Story," etc. These are structural guides for the LLM, not section headers in the output. The output must read as one continuous Henry narrative that happens to contain all 6 layers, NOT as "Hook: [text], Visual Journey: [text], Deep Thread: [text]." If the output has visible layer labels, it has FAILED.

**Why:** When the implementation prompt says "add explicit instructions for visual journey, one-sentence hook, wow detail, deep thread," an LLM agent may interpret "explicit" as "labeled." The current `content.ts` prompts correctly structure content as natural sections ("Guided Seeing," "The Hidden Detail"), but the roadmap's phrasing could lead an implementing agent to add explicit layer labels that would make the content sound mechanical rather than human.

**Safety invariant:** This is a clarification of existing prompt architecture. The content prompt structure in `src/lib/prompts/content.ts` already uses narrative section names. This fix ensures the roadmap does not override that pattern.

#### IF-5: Phase 3 -- Expand Visitor Personas from 3 to 5+

**Phase/Step:** Phase 3 Cycle Step 2 (Plan) and Cycle Step 4 (Validation)

**What to add:** Replace "3+ visitor personas" throughout Phase 3 with a specific expanded list:

> **User testing personas (minimum 5):**
> 1. Casual tourist (English, time-constrained, "what should I see?")
> 2. Art history enthusiast (deep knowledge, expert vocabulary)
> 3. Child-friendly mode (parent asking on behalf of a child)
> 4. Couple on a date (romantic context, shared exploration)
> 5. Quiet reflective visitor (minimal speech, long pauses, emotionally engaged)
>
> **Optional additional personas (if time permits):**
> 6. German-speaking visitor (if DE language is included -- test translation voice quality)
> 7. Rushed visitor who warms up mid-visit (test course correction)

**Why:** The design doc defines 6 detailed visitor types with worked examples. Testing with only 3 personas means half the adaptive system is unvalidated. The couple and quiet reflective visitor test fundamentally different adaptation dimensions (emotional register, pacing) that the tourist and expert do not cover.

**Safety invariant:** Adds test breadth. Does not change pipeline or code.

#### IF-6: Phase 3 -- Add German Conversation Test for Translation Voice Quality

**Phase/Step:** Phase 3 Cycle Step 4 (Validation -- Agent Functionality Tester)

**What to add:** After the existing Agent Functionality Tester instructions, add:

> If DE language is included in the Belvedere run: test a complete German conversation flow. Verify that Henry's warmth, guided seeing language, and storytelling voice survive translation. Specifically check: (a) does German Henry still use sensory directional language? ("Schauen Sie auf die Hande..."), (b) does he maintain conversational warmth or shift to formal/stiff German?, (c) are thought seeds and observational nudges natural in German? This is critical because the translation engine in `src/pipeline/translation.ts` uses Claude Sonnet -- the translation prompt must produce Henry-quality German, not textbook German.

**Why:** Belvedere is in Vienna. If DE is included (which the roadmap suggests Hermann decides), the German output is the most natural first-language test. But the validation step only specifies "test a basic conversation: greet Henry, ask about The Kiss, ask a follow-up." Without explicit German voice quality testing, the first German conversation with a real visitor becomes the test, which is too late.

**Impact on implementation:** May require refinement of the translation prompt in `src/pipeline/translation.ts` if German voice quality is inadequate.

#### IF-7: Phase 3 -- Specify API-Based Agent Verification

**Phase/Step:** Phase 3 Cycle Step 4 (Validation -- Agent Functionality Tester)

**What to add:** Replace "Test the deployed ElevenLabs agent: Verify the agent is live and responding" with:

> **Agent verification must be API-based, not voice-call-based:**
> - Verify agent exists: `curl -H "xi-api-key: $ELEVENLABS_API_KEY" "https://api.elevenlabs.io/v1/convai/agents/<AGENT_ID>"`
> - Verify V3 system prompt is active: check `conversation_config.agent.prompt.prompt` field in the API response
> - Verify KB documents uploaded: check `conversation_config.agent.prompt.knowledge_base` field
> - Verify turn_timeout is -1: check `conversation_config.turn.turn_timeout` field (per CLAUDE.md critical rules)
> - Verify skip_turn tool is enabled: check `conversation_config.agent.prompt.tools` field
> - Content tool test: This can only be tested via an actual conversation (voice or widget). The Agent Functionality Tester should initiate one test conversation and verify the content tool returns artifact data.

**Why:** The execution prompt is ambiguous about whether "test the deployed agent" means making voice calls or using the API. Voice testing by an LLM agent is impossible (it cannot speak into a phone). API verification is comprehensive, repeatable, and automatable.

#### IF-8: Phase 4 -- Explicitly Name `voice-optimize.ts` Alongside QA Stage

**Phase/Step:** Phase 4 Cycle Step 1 (Research -- Codebase Scanner and QA Alignment Analyst)

**What to add:** In the QA Alignment Analyst's instructions, add:

> Deep-read both the QA stage implementation (`src/pipeline/stages/05-quality-assurance.ts`) AND the voice quality prompt template (`src/lib/prompts/voice-optimize.ts`). The QA stage imports `CONVERSATIONAL_QUALITY_CHECK` from `voice-optimize.ts` (line 21 of the QA stage file). This template defines the scoring criteria (rhythm, length, engagement, accessibility, flow, guidedSeeing, discoveryEngagement). If V3 adds new quality dimensions (e.g., adaptive tone, invariant presence, anti-detection compliance), they must be added BOTH to this template AND to the QA stage's interpretation of the scores.

**Why:** The QA Alignment Analyst is told to "deep-read the QA stage and its prompt in `src/lib/prompts/`" but `voice-optimize.ts` is not in `src/lib/prompts/` in the way most agents would scan (they would look at `content.ts` and `intake.ts`). The file name `voice-optimize.ts` does not obviously connect to "QA voice quality criteria." Without explicit naming, the analyst may miss it.

#### IF-9: Phase 4 -- Enumerate All Files with Henry Voice Instructions

**Phase/Step:** Phase 4 Cycle Step 1 (Research -- Codebase Scanner)

**What to add:** Replace the Codebase Scanner's generic grep instructions with a concrete file inventory as a starting point:

> **Known files containing Henry voice/personality instructions (verify each, search for others):**
>
> | File | What it contains | V3 scope |
> |------|-----------------|----------|
> | `src/lib/prompts/agent-personality.ts` | ElevenLabs agent system prompt | Phase 1 (primary target) |
> | `src/lib/prompts/content.ts` | Content-write system prompt + all 4 entity prompts | Phase 2 (primary target) |
> | `src/lib/prompts/rewrite.ts` | Content generation prompt + voice optimization prompt | Phase 2 (must update) |
> | `src/lib/prompts/voice-optimize.ts` | Conversational quality check scoring criteria | Phase 4 (must align) |
> | `src/pipeline/stages/05-quality-assurance.ts` | Voice quality gate (imports from voice-optimize.ts) | Phase 4 (must align) |
> | `src/pipeline/stages/04-content-write.ts` | Anti-meta fallback text (line ~856) | Phase 4 (check V2 remnants) |
> | `src/lib/prompts/intake.ts` | Intake planning prompt (may reference voice style) | Phase 2 (check) |
> | `src/lib/prompts/discovery.ts` | Discovery synthesis prompt (may reference voice style) | Phase 4 (check) |
>
> Scan ALL files in `src/lib/prompts/` and grep for: "Henry", "warm", "grandfather", "companion", "guided seeing", "observational nudge", "thought seed", "museum companion", "world-leading expert" (V2 remnant).

**Why:** Without a concrete starting inventory, the Codebase Scanner must discover these files from scratch, which risks missing files that encode Henry's voice in non-obvious ways (like the anti-meta fallback text buried at line 856 of the content-write stage).

#### IF-10: Phase 5 -- Add Cost Reference Doc Path

**Phase/Step:** Phase 5 Cycle Step 1 (Research -- Cost & Infrastructure Analyst)

**What to add:** In the Cost & Infrastructure Analyst's instructions, add:

> Reference the existing cost analysis at `docs/reference/20260216_COST_ANALYSIS_AND_MODEL_SELECTION.md` for per-museum API cost baselines. The CLAUDE.md documents LLM model routing: content writing uses Claude Sonnet 4.5, fact extraction uses Claude Haiku 4.5. Standard mode targets ~300,000 chars output. Use these baselines to estimate re-run costs per museum per mode.

**Why:** The cost estimation task requires baseline data that already exists in the codebase but is not referenced in the execution prompt. Without it, the analyst will either search blindly or estimate from scratch, producing less accurate numbers.

#### IF-11: Phase 5 -- Warn Against Scope Creep into New Pipeline Code

**Phase/Step:** Phase 5 Cycle Step 3 (Implementation -- Migration Operator and Architect Overseer)

**What to add:** In the Migration Operator's rules:

> **SCOPE CONTROL:** Phase 5 is a MIGRATION phase, not a development phase. The Migration Operator must NOT write new pipeline code, modify existing stage implementations, or change database schema. The only allowed actions are: (a) triggering re-runs via existing API endpoints, (b) monitoring pipeline status via existing queries, (c) updating system prompt text via existing deployment mechanisms. If a bug is discovered during migration, STOP and document it. Do not fix infrastructure during a migration.

**Why:** Phase 5 runs 28 museums through the pipeline. The temptation to "fix" issues discovered during migration is high, but pipeline code changes during a migration create an inconsistency: some museums ran with the old code, others with the new. This must be explicitly forbidden.

**Safety invariant:** Preserves the pipeline infrastructure freeze principle from CLAUDE.md.

#### IF-12: Phase 5 -- Add Public API Monitoring During Migration

**Phase/Step:** Phase 5 Cycle Step 3 (Implementation) and Cycle Step 4 (Validation -- Regression Monitor)

**What to add:** In the Regression Monitor's scope:

> Monitor the public API (`GET /api/public/museums`) during and after each migration batch. Verify: (a) all museums are still listed, (b) all language variants have valid agent IDs, (c) response times are stable (no degradation from concurrent re-runs), (d) no museums show error states in the response. Run this check before each batch, immediately after each batch, and daily for one week after the final batch.

**Why:** The public API is what the mobile app consumes. If a migration temporarily removes or corrupts a museum's agent data, mobile app users experience immediate failure. The roadmap's validation step mentions "public API" once but does not specify what to check or when.

---

### Cross-Cutting Reference Fix

All 5 phases should reference the design doc to keep implementation agents grounded in the vision. The design doc is the "why"; the roadmap is the "how." Without explicit cross-referencing, execution agents may drift from the design's intent.

**What to add:** In each phase's CONTEXT block (the section at the top of each execution prompt, before the cycle steps), add the following reference paragraph:

> **Design anchor:** Every implementation decision in this phase must be evaluated against the Adaptive Personality System design document (`wiki/strategy/20260320-henrys-adaptive-personality-system.html`). This document defines the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, adaptation boundaries, and the Identity Test. If any implementation choice conflicts with the design doc, the design doc wins. The design doc is the "idea." This roadmap is the "how." The founding vision (`wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html`) provides the emotional truth behind the design.

**Where to add it in each phase:**

| Phase | Insert location |
|-------|----------------|
| Phase 1 | After the CONTEXT paragraph, before `---` leading to Cycle Step 1 |
| Phase 2 | After the narrative layers list, before `---` leading to Cycle Step 1 |
| Phase 3 | After the Belvedere context paragraph, before `---` leading to Cycle Step 1 |
| Phase 4 | After the CONTEXT paragraph, before `---` leading to Cycle Step 1 |
| Phase 5 | After the CONTEXT paragraph, before `---` leading to Cycle Step 1 |

Additionally, in Phase 1 Cycle Step 1, the Voice Architect should be instructed to read the design doc "end-to-end, including the six worked examples in 'The Six Visitors -- Henry in Action.'" These examples are the most concrete specification of what correct V3 behavior looks like.

---

## Part 3: Downstream Impact Analysis

| Changed document | Consumers | Needs update after hardening? |
|-----------------|-----------|-------------------------------|
| **Design doc** (Adaptive Personality System) | Implementation roadmap execution prompts, future V4 planning, wiki readers | Yes -- roadmap prompts must reference updated invariant count (12 boundaries vs. 10), expanded profiling model, and Identity Test as formal criterion |
| **Implementation roadmap** (execution prompts) | Executing agents (Claude Code sessions), Hermann (review/approval) | Yes -- all 6 critical fixes and 12 important fixes applied to prompt text |
| **`src/lib/prompts/agent-personality.ts`** | ElevenLabs agents for all museums, Stage 07 deployment | Changed in Phase 1 -- all 28+ museums receive updated system prompt via re-deployment or migration |
| **`src/lib/prompts/content.ts`** | Stage 04 (content-write), Stage 05 (QA coverage gate) | Changed in Phase 2 -- new narrative layer instructions; QA coverage targets unchanged |
| **`src/lib/prompts/rewrite.ts`** | Stage 04 (content-write voice optimization pass) | Changed in Phase 2 -- must align with V3 voice; currently missing from roadmap scope (CF-3 fixes this) |
| **`src/lib/prompts/voice-optimize.ts`** | Stage 05 (QA voice quality gate) | Changed in Phase 4 -- scoring criteria must include V3-specific dimensions |
| **`src/pipeline/stages/05-quality-assurance.ts`** | Pipeline orchestrator (Stage 05) | Interpretation of voice quality scores may need threshold adjustment in Phase 4 |
| **Translation engine** (`src/pipeline/translation.ts`) | Stage 07b (translation), manual translate API | NOT changed in V3 -- but Phase 3 German testing (IF-6) may reveal translation prompt needs refinement |
| **Mobile app** (AITourPilot4) | End users | No code change needed -- agents update transparently via ElevenLabs platform |
| **Public API** (`/api/public/museums`) | Mobile app, external consumers | No code change needed -- but must be monitored during Phase 5 migration (IF-12) |
| **CLAUDE.md** (project) | All development agents | Updated in Phase 4 to reflect V3 as default; prompt version references updated |

---

## Part 4: Risk Areas

### Risk #1: The V3 System Prompt Becomes a Rules Engine Instead of a Character Sheet

**What it is:** The most dangerous outcome of V3 implementation is that the system prompt, attempting to encode 9 invariants + 6 dimensions + 12 boundaries + progressive profiling + course correction + graceful recovery + engagement type ratios, becomes so dense with rules that the LLM treats Henry as a rule-following system rather than a character with intuition. The prompt reads like a compliance checklist. Henry sounds mechanical.

**Why it's dangerous:** This is the design doc's own warning: "If he adapts too much, he becomes a generic chatbot wearing different masks." Paradoxically, the more precisely we specify Henry's behavior, the more we risk creating exactly the mechanical persona the design rejects. The V2 prompt in `agent-personality.ts` is 134 lines and already feels dense. V3 will be larger.

**How this plan mitigates it:**
- The Prompt Writer instruction (Phase 1 Step 3) explicitly states: "The prompt should read like a character sheet for an actor, not a technical specification. If it reads like a rules engine, it's wrong."
- The Identity Test (elevated in design doc change 1.9, enforced in IF-2) provides a concrete quality gate: if the output could be any chatbot, it fails.
- The Consistency Guardian reviews for contradictions and over-specification, not just completeness.
- The Scenario Tester's adversarial tests (IF-3) verify that rules produce natural behavior, not robotic compliance.

**Residual risk:** Medium. The Prompt Writer must be skilled at encoding behavioral guidelines as character traits. Hermann's final voice review is the ultimate safeguard.

### Risk #2: Phase 5 Migration Degrades Live Museum Experiences

**What it is:** Re-running 28 museums replaces all KB content atomically (via the re-run pipeline's atomic KB swap). If V3 content is worse for a specific museum -- shorter, less accurate, or with a different voice than what visitors are accustomed to -- there is no gradual rollout. The museum's agent switches from V2 content to V3 content in one operation.

**Why it's dangerous:** Real users interact with these agents today. A regression in a popular museum (Albertina, Uffizi) affects actual visitor experiences. The atomic KB swap means the regression is immediate and total for that museum. Unlike a web deployment, there is no A/B testing or canary rollout for ElevenLabs agents.

**How this plan mitigates it:**
- CF-4 adds mandatory Supabase backup verification before migration begins, enabling point-in-time restore.
- IF-11 prevents pipeline code changes during migration, ensuring consistency across all 28 museums.
- IF-12 adds public API monitoring during and after migration batches.
- Phase 5's existing batch strategy (with per-batch quality spot-checks) provides early warning.
- The Phase 5 research step categorizes museums into tiers -- some may only need a prompt-swap without content re-run, significantly reducing risk.

**Residual risk:** Medium-high. The atomic KB swap cannot be undone without a full re-run to the old content. Supabase PITR restores the database but not the ElevenLabs KB state. The rollback path for a bad migration is: restore DB from PITR, then re-run the museum with the old V2 pipeline code (which would need to be preserved in a git branch). This rollback path should be explicitly documented in Phase 5 planning.

---

## Part 5: Verification Checklist

Use this checklist AFTER all hardening changes are applied to verify nothing was missed.

### Design Document Changes
- [ ] 1.1: Boundary #11 (disagreement handling) added to "Adaptation Boundaries" section
- [ ] 1.2: Boundary #12 (distress boundary) added to "Adaptation Boundaries" section
- [ ] 1.3: Cultural communication style awareness added to "Visitor Profile Model > Signal Sources"
- [ ] 1.4: Silence-as-positive-act callout added to "Progressive Profiling Model"
- [ ] 1.5: Proactive navigation guidance row added to "Dimension 3: Pacing & Density"
- [ ] 1.6: "What Henry Should NOT Detect" elevated and relabeled as "The Anti-Detection Rule"
- [ ] 1.7: Mid-conversation course correction expanded with signal-response pairs
- [ ] 1.8: Failure mode / graceful recovery expanded from open question to answered design decision
- [ ] 1.9: Identity Test elevated to formal validation criterion with explicit testing instruction
- [ ] 1.10: Cross-visit memory reframed as highest-impact V4 feature with technical path
- [ ] 1.11: Accessibility acknowledgment added as future consideration

### Roadmap -- Critical Fixes
- [ ] CF-1: Wiki server path context block added to Phase 1 Step 3, Phase 2 Step 3 execution prompts
- [ ] CF-2: ElevenLabs conversation log access -- fallback research path specified in Phase 1 Step 1
- [ ] CF-3: `rewrite.ts` added to Phase 2 scope (Steps 1 and 3) and Phase 4 scan (Step 1)
- [ ] CF-4: Supabase backup verification added to Phase 5 Step 2
- [ ] CF-5: Database access pattern block added to Phase 2, 3, 5 execution prompts
- [ ] CF-6: YYYYMMDD substitution instruction added to Execution Model section + all deliverable references

### Roadmap -- Important Fixes
- [ ] IF-1: Consistency Guardian checklist expanded with items (g) through (k) in Phase 1 Step 3
- [ ] IF-2: Identity Test added as mandatory Scenario Tester criterion in Phase 1 Step 4
- [ ] IF-3: 3 adversarial boundary-testing scenarios added to Phase 1 Step 4
- [ ] IF-4: "Layers are woven, not labeled" clarification added to Phase 2 Step 3
- [ ] IF-5: Visitor persona list expanded to 5+ in Phase 3 Steps 2 and 4
- [ ] IF-6: German conversation test specified in Phase 3 Step 4
- [ ] IF-7: API-based agent verification specified in Phase 3 Step 4
- [ ] IF-8: `voice-optimize.ts` explicitly named in Phase 4 Step 1
- [ ] IF-9: Complete file inventory with V3 scope provided in Phase 4 Step 1
- [ ] IF-10: Cost reference doc path added to Phase 5 Step 1
- [ ] IF-11: Scope creep warning added to Phase 5 Step 3
- [ ] IF-12: Public API monitoring added to Phase 5 Steps 3 and 4

### Cross-Cutting
- [ ] Design anchor paragraph added to all 5 phase CONTEXT blocks
- [ ] Voice Architect in Phase 1 instructed to read design doc end-to-end including Six Visitors examples

### Integrity Verification
- [ ] All boundary count references updated from 10 to 12 throughout roadmap
- [ ] No changes made to files listed in Part 6 (Files NOT to Touch)
- [ ] Every change in this plan traces to a specific analysis finding (no unbounded additions)

---

## Part 6: Files NOT to Touch

The following files and systems must NOT be modified as part of this hardening or during the V3 implementation, except where explicitly scoped by the roadmap (Phases 1-4 touch prompt files only):

### Pipeline Infrastructure
- `src/pipeline/orchestrator.ts` -- BullMQ job orchestration
- `src/lib/queue.ts` -- Queue configuration
- `src/pipeline/stages/00-intake.ts` -- Intake stage logic (prompt in `intake.ts` may be adjusted in Phase 2 research, but stage code is frozen)
- `src/pipeline/stages/00b-top-up-intake.ts` -- Top-up intake logic
- `src/pipeline/stages/00c-rerun-intake.ts` -- Re-run intake logic
- `src/pipeline/stages/01-source-discovery.ts` -- Source discovery
- `src/pipeline/stages/02-deep-research.ts` -- Deep research
- `src/pipeline/stages/03-copyright-check.ts` -- Copyright check
- `src/pipeline/stages/06-data-structure.ts` -- Data structuring
- `src/pipeline/stages/06b-current-info-research.ts` -- Operational data research
- `src/pipeline/stages/07-elevenlabs-deploy.ts` -- ElevenLabs deployment (agent configuration, KB upload, tool setup)
- `src/pipeline/stages/07b-translation.ts` -- Translation stage
- `src/pipeline/stages/08-reporting.ts` -- Reporting
- `src/lib/heartbeat.ts` -- Heartbeat mechanism
- `src/lib/fetch-timeout.ts` -- Fetch timeout utility
- `scripts/fix-orphans.ts` -- Orphan detector

### Database
- `prisma/schema.prisma` -- Database schema (no new tables, no column changes)
- `prisma/migrations/` -- No new migrations required for V3

### External Service Integrations
- `src/integrations/` -- All external service clients (ElevenLabs, LLMs, search APIs)
- `src/lib/constants/agent-defaults.ts` -- Agent configuration defaults (turn_timeout, etc.)

### Legal/Copyright Engine
- `src/pipeline/legal/` -- Copyright classifier, plagiarism checker, audit system
- `src/lib/prompts/copyright.ts` -- Copyright compliance prompts
- `src/lib/prompts/copyright-check.ts` -- Copyright check prompts

### Translation & Operational Data
- `src/pipeline/translation.ts` -- Translation engine (may be refined in Phase 3 if German testing reveals issues, but NOT as part of hardening)
- `src/pipeline/operational-refresh.ts` -- Weekly operational data refresh
- `src/pipeline/operational-layers.ts` -- ElevenLabs operational sync

### Content Factory UI
- `src/app/` -- All Next.js pages and API routes (no UI changes for V3)

### Cloud Infrastructure
- Vercel deployment configuration
- Render worker configuration
- Supabase database (read-only during research; backup before Phase 5 migration)
- Upstash Redis configuration
- Cloudflare R2 storage configuration

---

*This hardening plan is a companion to the [Henry V3 Implementation Roadmap](wiki/strategy/20260402-henry-v3-adaptive-personality-implementation-roadmap.html). Apply all changes in this plan before executing Phase 1. The plan ensures that the roadmap faithfully implements the [Adaptive Personality System design](wiki/strategy/20260320-henrys-adaptive-personality-system.html) without dilution, and that execution prompts contain the operational details necessary for autonomous agent execution.*
