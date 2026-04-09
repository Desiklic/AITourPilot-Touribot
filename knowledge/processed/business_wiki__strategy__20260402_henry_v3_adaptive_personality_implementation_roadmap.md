# 20260402-henry-v3-adaptive-personality-implementation-roadmap

*Source: Business Wiki / strategy/20260402-henry-v3-adaptive-personality-implementation-roadmap.html*

## Context

This document is the implementation roadmap for the [Henry Adaptive Personality System](20260320-henrys-adaptive-personality-system.html), which defines Henry's immutable core (9 invariants), 6 adaptive dimensions, progressive visitor profiling, and hard adaptation boundaries.

**Key reference documents:**
- **Adaptive Personality System design:** [Henry's Adaptive Personality System](20260320-henrys-adaptive-personality-system.html)
- **Founding vision:** [The Soul of AITourPilot -- How Henry Was Born](20260320-henry-vision-the-soul-of-aitourpilot.html)
- **User Testing Evidence:** \\`docs/dev-specs/20260405_USER_TESTING_ANALYSIS.md\\` -- 68 real conversations from KHM Wien and Albertina (March-April 2026). Empirical foundation for V3 prompt requirements.

The design is complete. This document lays out the **phased path from design to production** -- what to build, in what order, and how to validate each step.

### Execution Model

Each phase is executed by a multi-agent team following a 4-step cycle:

| Step | What | Who decides |
|------|------|-------------|
| **Research** | Gather context, read existing code/content, identify constraints and options | Agent team |
| **Planning** | Produce a concrete plan with file-level changes, dependencies, and risk assessment | Agent team, reviewed by Hermann |
| **Implementation** | Execute the plan -- code changes, prompt writing, pipeline runs | Agent team |
| **Validation** | Verify correctness -- tests, output review, quality gates, user testing where noted | Agent team + Hermann |

Phases are **sequential** -- each phase's validation must pass before the next phase begins. Within a phase, the 4 steps run in order.

**File naming convention:** All deliverable files use the pattern \\`docs/dev-specs/YYYYMMDD_*.md\\` where YYYYMMDD is the actual date of creation in ISO format (e.g., \\`20260407\\`). Replace \\`YYYYMMDD\\` with today's date when creating the file. Do not use the literal string "YYYYMMDD" as a filename.

---

## Phase 1: Henry V3 System Prompt

**Goal:** Write the new ElevenLabs agent system prompt that embeds the Adaptive Personality System into Henry's character.

**Why first:** The system prompt is the single most impactful artifact. It defines how Henry behaves regardless of what content the KB contains. Every subsequent phase depends on this being right.

### Research
- Review the current V2 system prompt (`src/lib/prompts/agent-personality.ts`)
- Review the Adaptive Personality System design doc (9 invariants, 6 dimensions, boundaries, visitor profiling model)
- Review the Henry Vision blog entry (the founding principles)
- Analyze real visitor interaction patterns with Henry (conversation transcripts from Hermann, or hypothetical flows based on design doc visitor types if transcripts unavailable)
- Identify what V2 already does well vs. what's missing

### Planning
- Define the V3 prompt structure (which sections stay, which are new, which are rewritten)
- Define the new ADAPTATION section with concrete behavioral anchors
- Define the new BOUNDARIES section (the 12 "nevers")
- Draft the prompt in a planning document for review before committing

### Implementation
- Write the V3 system prompt in `src/lib/prompts/agent-personality.ts`
- Store the V3 prompt as a wiki entry under **Prompts > Content Pipeline V3 -- Henry Adaptive** (new prompt folder)
- Version the prompt clearly: V2 = current, V3 = adaptive personality
- Update any constants or references that point to the prompt

### Validation
- Side-by-side comparison: V2 vs V3 prompt against the 9 invariants checklist
- Verify all 6 adaptive dimensions have concrete behavioral instructions
- Verify all 12 boundary rules are explicitly encoded
- Verify the prompt stays within reasonable token count for ElevenLabs (system prompt size affects latency)
- Hermann reviews the prompt for voice and soul

**Exit criteria:** V3 prompt approved by Hermann, stored in codebase and wiki.

### Execution Prompt

> **Copy and execute this complete prompt to run Phase 1. All 4 cycle steps are included.**

---

**CONTEXT:** We are implementing the Henry V3 Adaptive Personality System for AITourPilot's museum companion. Henry is a warm, deeply knowledgeable guide inspired by a grandfather figure. The V2 system prompt (current) is in `src/lib/prompts/agent-personality.ts`. The design documents defining what V3 should be:
- **Adaptive Personality System design:** `wiki/strategy/20260320-henrys-adaptive-personality-system.html` (9 invariants, 6 adaptive dimensions, visitor profiling, 12 boundaries)
- **Henry Vision (founding principles):** `wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html`
- **User testing analysis (68 real conversations):** \\`docs/dev-specs/20260405_USER_TESTING_ANALYSIS.md\\` -- Evidence from KHM Wien and Albertina testing sessions. Contains specific prompt instructions grounded in real visitor behavior, the "golden exchange" (Conv 34) that demonstrates ideal V3 behavior, and quantitative data on response length, interruption rates, and engagement patterns. **This is the empirical foundation for the V3 prompt -- read it end-to-end.**
- **Project context:** `CLAUDE.md` at the content-factory repo root

The goal: Write a new V3 system prompt that embeds the full adaptive personality into Henry's character -- making him adapt to wildly different visitors (child, expert, rushed tourist, grieving person) while remaining unmistakably Henry.

**Design anchor:** Every implementation decision in this phase must be evaluated against the Adaptive Personality System design document (\\`wiki/strategy/20260320-henrys-adaptive-personality-system.html\\`). This document defines the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, adaptation boundaries, and the Identity Test. If any implementation choice conflicts with the design doc, the design doc wins. The design doc is the "idea." This roadmap is the "how." The founding vision (\\`wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html\\`) provides the emotional truth behind the design.

---

#### Cycle Step 1 -- RESEARCH

GOAL: Thoroughly understand the current V2 prompt, the V3 design requirements, and what constraints exist before writing the V3 prompt. I need a clear, complete picture.

Create an agent team of 3 teammates using Sonnet:

1. **V2 Prompt Analyst** -- Read `src/lib/prompts/agent-personality.ts` end-to-end. Map every section of the current V2 prompt. Document what character traits are defined, what engagement rules exist, what response rules are set, what's hardcoded vs. parameterized. Then cross-reference against the Adaptive Personality System design doc and produce a gap analysis: what does V3 require that V2 doesn't have? Be specific -- section by section. Analyze real visitor interaction patterns with Henry. Hermann will provide 3-5 exported ElevenLabs conversation transcripts from existing museums (Albertina, Uffizi, or similar) as text files before this step begins. If conversation logs are not available, the V2 Prompt Analyst should instead: (a) review the Six Visitors worked examples in the design doc, (b) study the current system prompt's engagement rules, and (c) generate 3 hypothetical but realistic conversation flows based on the design doc's visitor types to identify what the V2 prompt would handle well vs. poorly. Flag this as a research gap and document assumptions. Also read the user testing analysis (\\`docs/dev-specs/20260405_USER_TESTING_ANALYSIS.md\\`) for evidence of V2's real-world strengths and failures. Pay special attention to Section 7.1 (Phase 1 findings) which contains 7 specific prompt instructions grounded in conversation data, and Appendix A which contains the "golden exchange" (Conv 34) -- the single best example of what V3 should produce.

2. **Voice Architect** -- Read both design documents (Adaptive Personality System + Henry Vision) end-to-end, including the six worked examples in "The Six Visitors -- Henry in Action." These examples are the most concrete specification of what correct V3 behavior looks like. Synthesize the complete V3 requirements: the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, 12 boundary rules, and the three engagement types (Observational Nudges, Thought Seeds, Rare Genuine Questions). Also read the current content pipeline prompts (`src/lib/prompts/content.ts`) to understand what content Henry has to work with. Think about prompt architecture: how should these requirements be structured in a system prompt that's effective for an LLM?

3. **ElevenLabs Constraints Researcher** -- Research ElevenLabs conversational AI system prompt best practices. How does system prompt length affect latency? Are there known patterns for adaptive personas in voice AI? Also check the current agent configuration in `src/lib/constants/agent-defaults.ts` and `src/pipeline/stages/07-elevenlabs-deploy.ts` for constraints the prompt must respect (turn_timeout, skip_turn, tool use patterns).

Each teammate: Take your time. Read full files, not just grep results. When you find something important, message your teammates immediately.

DELIVERABLES:
- Each teammate sends findings to the Voice Architect
- The Voice Architect produces a consolidated research summary: (a) V2 current state with section-by-section assessment, (b) gap analysis against V3 requirements, (c) ElevenLabs constraints, (d) recommended V3 prompt architecture (sections, ordering, approximate token budget)
- Save as `docs/dev-specs/<YYYYMMDD>_HENRY_V3_PROMPT_RESEARCH.md` (replace <YYYYMMDD> with today's date, e.g., 20260407)

COORDINATION: The V2 Prompt Analyst shares findings with the Voice Architect as they map each section. The Voice Architect challenges: "Does this V2 section adequately cover invariant #X?" and "How would this handle the rushed tourist vs. grieving visitor?"

---

#### Cycle Step 2 -- PLAN

Based on the research just completed, write the V3 prompt design plan.

This is not code -- it's the most important piece of text in the entire product. The system prompt IS Henry. It must be:
- Authentic and warm, not mechanical or rule-heavy
- Structured so the LLM can follow it reliably under real-time voice conversational pressure
- Compact enough to not degrade ElevenLabs response latency
- Complete enough that Henry never breaks character, even in edge cases

Create the plan as `docs/dev-specs/<YYYYMMDD>_HENRY_V3_PROMPT_PLAN.md` (replace <YYYYMMDD> with today's date, e.g., 20260407).

STRUCTURE:
1. V3 prompt section outline (ordered list of sections with purpose and approximate token budget)
2. For each section: what stays from V2, what's rewritten, what's new
3. The ADAPTATION section draft -- this is the core new section, write it in full
4. The BOUNDARIES section draft -- the 12 "nevers" in prompt-ready language
5. Prompt size estimate vs. ElevenLabs constraints
6. What the V3 prompt deliberately does NOT include (scope control)

ALSO INCLUDE:
- Side-by-side comparison table: V2 sections to V3 sections
- Risk areas: #1 risk is the prompt being too long/complex for the LLM to follow reliably. #2 risk is adaptation instructions overriding the core identity.
- How to test: describe 3 test conversations (child, expert, rushed tourist) and what good Henry responses look like

**EVIDENCE-BASED PROMPT REQUIREMENTS (from user testing):**

The V3 system prompt MUST include these specific instructions, each grounded in real conversation evidence:

1. **First-response cap: 60-80 words.** Overall ceiling remains 100 words, but the FIRST response to any new artwork must be shorter -- one visual anchor and one hook, then wait. (Evidence: 56% interruption rate on 130+ word first responses)

2. **Request-type matching.** Henry must detect what kind of answer the visitor wants (identification, narrative, visual guidance, hook, practical) and match his response structure. Do NOT default to visual guidance for every question. (Evidence: Conv 1 -- visitor wanted "who is Martha" and got atmosphere; Conv 6 -- visitor explicitly asked for less visual guidance)

3. **Open Door frequency cap.** The "if you'd like to hear more" invitation appears at most once per 3 exchanges. Vary the phrasing each time. (Evidence: 55 occurrences across 68 conversations, 49% received no response)

4. **Visual guidance vocabulary rotation.** Never use the same guided-seeing phrase ("Look at..." / "Schauen Sie auf...") more than twice in one conversation. Maintain 5-6 alternative phrasings. (Evidence: "Schauen Sie zuerst auf..." appeared in 67% of conversations)

5. **Artwork context stickiness.** Once a visitor has named an artwork, Henry stays in that artwork's context until the visitor explicitly moves to a new one. Do NOT guess a different artwork based on ambiguous speech. (Evidence: Conv 4 -- Henry guessed Arcimboldo when visitor had clearly stated Rubens)

Hermann reviews and approves this plan before the prompt is written.

---

#### Cycle Step 3 -- IMPLEMENT

GOAL: Write the Henry V3 system prompt and deploy it.

Create an agent team of 3:

1. **Prompt Writer** -- Write the V3 system prompt following the approved plan. This is creative writing with technical constraints -- Henry's voice must come through in the prompt itself. The prompt should read like a character sheet for an actor, not a technical specification. Write it in `src/lib/prompts/agent-personality.ts`, replacing the `buildPrompt()` function's return value. Preserve the function signature and parameter handling (museumName, museumSpecialty, language, operationalSnapshot).

2. **Consistency Guardian** -- Does NOT write the prompt. Reads every line the Prompt Writer produces and verifies: (a) all 9 invariants are present, (b) all 6 adaptive dimensions have behavioral anchors, (c) all 12 boundaries are encoded, (d) the three engagement types are described with correct ratios, (e) no contradictions, (f) museum-awareness and emotional-presence sections preserved, (g) the progressive profiling model is encoded (warm baseline turns 1-2, calibration turns 3-5, tuned turn 6+, never locks in), (h) the "What Henry Should NOT Detect" anti-detection list is present and positioned prominently, (i) mid-conversation course correction behaviors are encoded with specific signal-response pairs, (j) graceful recovery from misjudgment is encoded (invisible adjustment, never announced), (k) disagreement handling boundary (#11) and distress boundary (#12) are encoded. Flag gaps immediately.

3. **Wiki Publisher** -- Store the V3 prompt in the wiki. Create a new prompt folder `prompts/content-pipeline-v3-henry/` and publish the agent system prompt V3. Use the wiki server API at port 8777 (see wiki CLAUDE.md for instructions). Pass raw, unescaped markdown -- the server handles escaping. Also update any references in `CLAUDE.md`.

WIKI SERVER CONTEXT:
- The wiki is at: /Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/
- The wiki CLAUDE.md with full API instructions is at: /Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/CLAUDE.md
- The server runs on http://localhost:8777 -- all article CRUD goes through this API (never edit files directly)
- To create articles: POST to /api/create with { category, slug, title, markdown, ... }
- The V3 prompt folder will be: prompts/content-pipeline-v3-henry/ (a subfolder of the existing "prompts" category)
- The wiki server must be running before the Wiki Publisher can operate: cd to the wiki root and run \\`python server.py\\`

RULES:
- The Prompt Writer writes a first draft, the Consistency Guardian reviews, the Prompt Writer revises. At least 2 review cycles before finalizing.
- Do NOT change the function signature or the temporal context / language / operational injection sections -- those are infrastructure.
- The completed prompt must be warm and human-sounding. If it reads like a rules engine, it's wrong.

DELIVERABLE: V3 system prompt committed to codebase and published to wiki. Consistency Guardian confirms all requirements met.

---

#### Cycle Step 4 -- VALIDATE

GOAL: Validate the V3 system prompt against design requirements and real-world conversation scenarios.

Create an agent team of 2:

1. **Invariant Auditor** -- Systematic checklist review:
   - Read the V3 prompt end-to-end
   - For each of the 9 invariants: quote the specific prompt text that encodes it. If missing or weak, flag with a FAIL
   - For each of the 6 adaptive dimensions: quote the behavioral anchors. Verify they're concrete enough for an LLM to act on
   - For each of the 12 boundaries: quote the encoding. Verify unambiguous
   - Check for contradictions between rules
   - Verify prompt token count vs. ElevenLabs constraints
   - Produce structured pass/fail verdict

2. **Scenario Tester** -- Mental simulation of 6 visitor conversations:
   - Simulate how an LLM following this prompt would respond to: (a) a child saying "What's this?", (b) an expert saying "Ah, the Feldhase", (c) a tourist saying "We have 20 minutes", (d) a couple saying "Is this famous?", (e) a quiet person saying "Tell me about this one", (f) a parent saying "Can you tell us? My son is learning about the Renaissance"
   - Also simulate 3 adversarial scenarios: (g) A rude visitor: "This museum is boring. Why would anyone care about this old stuff?" -- Verify Henry stays warm, does not match sarcasm, and finds a genuine entry point. (h) An off-topic visitor: "What's a good restaurant near here? Also, what do you think about politics?" -- Verify Henry redirects warmly to art without being dismissive. (i) A visitor who disagrees: "I don't think this painting is beautiful at all. It looks like a child drew it." -- Verify Henry engages with their perspective rather than correcting them.
   - For each: write Henry's likely response given the V3 prompt. Evaluate against the design doc's worked examples.
   - Produce verdict: does the prompt reliably produce Henry-quality responses across all 9 scenarios?
   - **Identity Test (MANDATORY):** For each of the 9 simulated responses, apply the Identity Test from the design doc: strip the visitor's words and read Henry's response cold. If the response could have been produced by a generic museum chatbot (Musement, Bloomberg Connects, any audio guide), it FAILS the Identity Test. Document specifically what in each response makes it recognizably Henry -- not just warm, but uniquely Henry: the gentle opinions, the "even now" wonder, the story-over-facts instinct, the specific voice rhythms.

DELIVERABLE: Each validator produces a structured verdict (PASS or FAIL with specific issues). If ANY fails, fix and re-validate.

AFTER VALIDATION: Hermann receives the V3 prompt for final voice/soul review. The prompt is not done until Hermann approves.

---

## Phase 2: Content Pipeline Enrichment

**Goal:** Update the content-write prompts (Stage 04) so the pipeline produces richer content with the narrative layers Henry V3 needs to adapt.

**Why second:** The V3 prompt tells Henry *how* to adapt, but he needs *material* to adapt with. The KB content must include visual journeys, hooks, wow details, and deep threads so Henry can select the right layer for each visitor.

### Research
- Read the current content-write prompts (`src/lib/prompts/content.ts`) in detail
- Review 5-10 actual artifact KB documents from existing museums (Albertina, Uffizi, etc.) to assess which narrative layers are already present vs. missing
- Identify the gap between what the Adaptive Personality System design doc calls for and what the pipeline currently produces
- Check whether the intake prompt (`src/lib/prompts/intake.ts`) needs changes to gather the right source material

### Planning
- Define the specific prompt changes needed for each content type:
  - **Artifact content prompt:** Add explicit instructions for visual journey, one-sentence hook, wow detail, deep thread
  - **Museum overview prompt:** Ensure it gives Henry opening material for the greeting and museum-wide narrative threads
  - **Person biography prompt:** Ensure it produces human stories Henry can weave into artifact discussions
  - **Exhibition prompt:** Ensure it provides connection threads between artworks
- Assess whether discovery prompts (hidden connections, cross-references) need adjustment
- Define what "good output" looks like -- write 2-3 golden examples of enriched artifact content

### Implementation
- Update the content-write prompts in `src/lib/prompts/content.ts`
- Update any related prompts (intake, discovery) if needed
- Store the V3 content prompts as wiki entries under the new V3 prompt folder
- Ensure changes are backward-compatible -- existing museums' content should still work with V3 prompts (they just won't have the new layers until re-run)

### Validation
- Dry-run: Generate content for 2-3 artifacts using the new prompts against existing research data (no full pipeline run needed)
- Compare old vs. new output: verify the new narrative layers are present
- Verify existing content still works with the V3 system prompt (degraded but functional)
- Verify token/character counts are within acceptable range (no content bloat)

**Exit criteria:** Updated content prompts produce artifact content with all 6 narrative layers. Golden examples approved by Hermann.

### Execution Prompt

> **Copy and execute this complete prompt to run Phase 2. All 4 cycle steps are included.**

---

**CONTEXT:** The Henry V3 system prompt is complete and approved (Phase 1 done). Henry now knows HOW to adapt, but he needs richer content MATERIAL to adapt WITH. The content pipeline (Stage 04 -- content-write) produces artifact KB documents that Henry retrieves during conversations. These documents need to include multiple narrative layers so Henry can select the right one for each visitor type.

Required narrative layers per artifact (from the Adaptive Personality System design):
1. **Visual journey** -- guided-seeing passage directing the visitor's eye across the work
2. **The hook** -- one sentence that makes anyone want to know more (rushed tourist entry point)
3. **The human story** -- the artist as a person, not a Wikipedia entry
4. **The deep thread** -- art-historical connection or technique detail for expert visitors
5. **The wonder moment** -- the "wow" detail (window in the hare's eye, hidden signature)
6. **The connection thread** -- how this piece relates to others in the museum
7. **Quick identification** -- who/what/when in 2 sentences maximum. For paintings with multiple figures: who is each person. For group scenes: what is happening. For abstract works: what the artist titled it and when. This layer exists so Henry can answer "what am I looking at?" questions without delivering a narrative arc. (Evidence: visitors frequently asked basic identification questions that Henry answered with 130-word atmospheric responses instead of a simple "That's Martha on the left and Magdalena kneeling on the right.")

**Design anchor:** Every implementation decision in this phase must be evaluated against the Adaptive Personality System design document (\\`wiki/strategy/20260320-henrys-adaptive-personality-system.html\\`). This document defines the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, adaptation boundaries, and the Identity Test. If any implementation choice conflicts with the design doc, the design doc wins. The design doc is the "idea." This roadmap is the "how." The founding vision (\\`wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html\\`) provides the emotional truth behind the design.

DATABASE ACCESS:
- For read-only queries: use \\`psql $DATABASE_URL\\` with the queries from CLAUDE.md
- Example: psql $DATABASE_URL -c "SELECT name, description FROM artifacts WHERE museum_id = '<id>' LIMIT 5;"
- For browsing: run \\`yarn db:studio\\` to open Prisma Studio at http://localhost:5555
- The DATABASE_URL environment variable is in .env (never commit or log it)
- All production data access must be read-only during research steps. Write operations only during implementation.

---

#### Cycle Step 1 -- RESEARCH

GOAL: Understand what the content pipeline currently produces vs. what Henry V3 needs. Identify the exact gaps in each content prompt.

Create an agent team of 3 teammates using Sonnet:

1. **Content Prompt Analyst** -- Read every content-generation prompt in \\`src/lib/prompts/content.ts\\` in full. Map what each prompt asks for: artifact content prompt, museum overview prompt, person biography prompt, exhibition prompt. Document the exact output structure each prompt produces. Also read the intake prompt (\\`src/lib/prompts/intake.ts\\`) and discovery prompts to understand what source material feeds into content writing. Also read \\`src/lib/prompts/rewrite.ts\\` (contains \\`CONTENT_GENERATION_PROMPT\\` and \\`VOICE_OPTIMIZATION_PROMPT\\` used in the voice optimization pass during Stage 4). These must be updated alongside \\`content.ts\\` to avoid contradictory voice instructions.

2. **KB Output Reviewer** -- Query the database for 5-10 actual artifact records from completed museums (Albertina, Uffizi, or any COMPLETED museum). Read the \\`contentMarkdown\\` field of real artifacts. Assess each against the 6 narrative layers: which layers are already present? Which are consistently missing? Be specific -- quote examples of good visual journeys that already exist, and note where hooks or deep threads are absent.

3. **Pipeline Flow Tracer** -- Trace the full data flow from Stage 01 (source discovery) through Stage 04 (content-write) to Stage 06 (data-structure) to Stage 07 (ElevenLabs deploy). Understand what data is available at content-write time (facts, sources, discovery connections, person bios). Identify whether the content-write stage has access to everything it needs to produce the 6 narrative layers, or whether upstream stages need adjustment.

DELIVERABLES:
- Consolidated research summary: (a) current prompt structure and output format, (b) gap analysis -- which narrative layers exist vs. missing, with real examples, (c) upstream data availability, (d) recommended prompt changes per content type
- Save as \\`docs/dev-specs/<YYYYMMDD>_CONTENT_PIPELINE_V3_RESEARCH.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407)

---

#### Cycle Step 2 -- PLAN

Based on the research, write a phased implementation plan for content prompt enrichment.

This is a production content pipeline processing real museums. Changes must be backward-compatible -- existing museum content must still work.

Create the plan as \\`docs/dev-specs/<YYYYMMDD>_CONTENT_PIPELINE_V3_PLAN.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407).

STRUCTURE for each change:
1. Goal (one sentence)
2. File to modify (with specific function or prompt template)
3. What changes and why -- include the actual prompt additions or rewrites
4. Safety invariants: existing content must not break, token/character output must stay within KB limits, copyright compliance prompts must not be affected
5. How to verify: describe a dry-run test comparing old vs. new output

ALSO INCLUDE:
- 2-3 golden examples of what enriched artifact content should look like (write actual sample paragraphs that demonstrate all 6 narrative layers)
- Downstream impact: does Stage 05 (QA) need to check for the new layers? Does Stage 06 (data-structure) formatting change?
- Files NOT to touch: legal/copyright prompts, operational data prompts, translation prompts

---

#### Cycle Step 3 -- IMPLEMENT

GOAL: Update the content pipeline prompts to produce V3-quality content with all 6 narrative layers.

Create an agent team of 3:

1. **Prompt Implementer** -- Update the prompts in \\`src/lib/prompts/content.ts\\` following the plan. For each content type (artifact, museum overview, person biography, exhibition), add explicit instructions for the missing narrative layers. The writing voice must match Henry V3 -- warm, sensory, story-driven. Also update intake or discovery prompts if the research identified upstream gaps. Also update \\`src/lib/prompts/rewrite.ts\\` -- both the \\`CONTENT_GENERATION_PROMPT\\` and \\`VOICE_OPTIMIZATION_PROMPT\\` must align with V3 narrative layer requirements and Henry's voice.

   **CRITICAL:** The 6 narrative layers (visual journey, hook, human story, deep thread, wonder moment, connection thread) must be WOVEN into the content as a natural narrative -- NOT added as labeled sections. The artifact content prompt already structures content as "Guided Seeing," "The Hidden Detail," "The Human Story," etc. These are structural guides for the LLM, not section headers in the output. The output must read as one continuous Henry narrative that happens to contain all 6 layers, NOT as "Hook: [text], Visual Journey: [text], Deep Thread: [text]." If the output has visible layer labels, it has FAILED.

2. **Architect Overseer** -- Does NOT write prompts. Reviews every change for: (a) backward compatibility -- will existing museums' content still work? (b) no unintended side effects on legal/copyright prompts, (c) output size -- enriched content shouldn't blow up KB document sizes, (d) the prompt changes actually produce the intended layers (not just mentioning them but instructing the LLM how to write them).

3. **Wiki Publisher** -- Store all V3 content prompts in the wiki under \\`prompts/content-pipeline-v3-henry/\\`. Use the server API at port 8777. Pass raw unescaped markdown.

WIKI SERVER CONTEXT:
- The wiki is at: /Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/
- The wiki CLAUDE.md with full API instructions is at: /Users/hermannkudlich/Desktop/AITourPilot Project/BUSINESS_CONTENT/wiki/CLAUDE.md
- The server runs on http://localhost:8777 -- all article CRUD goes through this API (never edit files directly)
- To create articles: POST to /api/create with { category, slug, title, markdown, ... }
- The V3 prompt folder will be: prompts/content-pipeline-v3-henry/ (a subfolder of the existing "prompts" category)
- The wiki server must be running before the Wiki Publisher can operate: cd to the wiki root and run \\`python server.py\\`

DELIVERABLE: Updated content prompts committed. Architect confirms backward compatibility. Wiki updated.

---

#### Cycle Step 4 -- VALIDATE

GOAL: Verify the updated prompts produce content with all 6 narrative layers without regressions.

Create an agent team of 2:

1. **Content Quality Validator** -- Take 3 real artifacts from existing museums (e.g., Durer's Young Hare from Albertina, Klimt's The Kiss, one lesser-known piece). Using the NEW prompts and existing research data, generate content for each. Verify each output contains: (a) visual journey passage, (b) one-sentence hook, (c) human story, (d) deep thread, (e) wonder moment, (f) connection thread. Score each layer as present/partial/missing.

2. **Regression Checker** -- Verify that: (a) the prompt changes compile (no TypeScript errors), (b) existing museum content still renders correctly with the V3 system prompt (test by reading existing KB docs), (c) no legal/copyright prompts were accidentally modified, (d) output character counts are within acceptable range (not 2x larger than before).

DELIVERABLE: Structured verdict per validator (PASS/FAIL). The golden examples from the plan should be compared against actual output. Hermann reviews the generated content samples for voice quality.

---

## Phase 3: Belvedere Preparation & Pipeline Run

**Goal:** Run a Standard-mode pipeline for Belvedere (paintings collection only) as the first full test of the V3 adaptive system.

**Why Belvedere:** It's a world-class painting collection with diverse periods and styles -- Klimt, Schiele, Baroque, Medieval. This tests Henry's adaptation across very different artistic contexts. Standard mode produces enough content to validate depth without the cost of a Full run.

**Why paintings only:** Belvedere also has decorative arts, architecture, and sculpture. Scoping to paintings keeps the test focused on the core experience (visitor standing in front of a painting with Henry) while reducing run cost and time.

### Research
- Verify Belvedere is not already in the database (or if a previous Light run exists, assess its data)
- Research Belvedere's painting collection: key works, periods represented, gallery layout if available
- Determine how to scope to "paintings only" in the intake -- does the intake prompt support collection filtering? Does it need a `specialInstructions` parameter?
- Estimate Standard-mode cost and duration for a paintings-focused Belvedere run
- Review the re-run pipeline to understand if a fresh run or re-run is appropriate

### Planning
- Define the Belvedere run configuration: mode (Standard), target piece count, special instructions (paintings only), target languages (EN only for testing, or EN + DE since it's Vienna?)
- Define the quality checklist for output validation -- what does "good" look like for each artifact?
- Plan the user testing protocol: who tests, what devices, what scenarios (child, expert, rushed, etc.), how feedback is collected
- Identify any pipeline changes needed for the paintings-only scope

### Implementation
- Configure and trigger the Belvedere Standard pipeline run
- Monitor the run through all stages (intake through ElevenLabs deploy)
- Deploy the Belvedere agent with the V3 system prompt

### Validation
- **Pipeline output check (agent team):**
  - Review 10+ artifact KB documents for narrative layer completeness (visual journey, hook, wow detail, deep thread, connection threads)
  - Verify the museum overview provides a strong opening for Henry
  - Check content quality against the Henry Voice criteria (warmth, visual guidance, story arcs, no clinical language)
  - Verify ElevenLabs agent is deployed and functional
- **User testing (Hermann):**
  - Test the Belvedere agent in at least 3 different visitor personas (e.g., casual tourist, art expert, child-friendly)
  - Evaluate whether Henry adapts tone, depth, and story selection appropriately
  - Evaluate whether Henry maintains his core identity across all personas
  - Note specific artifacts where the content or adaptation falls short
- **Iterate:** If validation surfaces issues, loop back to the relevant phase (prompt adjustments go to Phase 1, content issues go to Phase 2, pipeline issues stay in Phase 3)

**Exit criteria:** Belvedere agent passes both automated quality checks and Hermann's user testing across 5+ visitor personas. Henry is unmistakably Henry in all interactions, AND he adapts appropriately to different visitors.

### Execution Prompt

> **Copy and execute this complete prompt to run Phase 3. All 4 cycle steps are included.**

---

**CONTEXT:** Henry V3 system prompt (Phase 1) and enriched content prompts (Phase 2) are complete. Now we need a real-world test: run the full pipeline for Belvedere (paintings collection only) in Standard mode to validate the entire V3 system end-to-end.

Belvedere is a world-class Viennese museum with diverse periods (Medieval, Baroque, Klimt/Schiele, contemporary). Standard mode produces ~50,000 words -- enough to validate depth. Paintings-only scope keeps cost manageable.

**Design anchor:** Every implementation decision in this phase must be evaluated against the Adaptive Personality System design document (\\`wiki/strategy/20260320-henrys-adaptive-personality-system.html\\`). This document defines the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, adaptation boundaries, and the Identity Test. If any implementation choice conflicts with the design doc, the design doc wins. The design doc is the "idea." This roadmap is the "how." The founding vision (\\`wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html\\`) provides the emotional truth behind the design.

DATABASE ACCESS:
- For read-only queries: use \\`psql $DATABASE_URL\\` with the queries from CLAUDE.md
- Example: psql $DATABASE_URL -c "SELECT name, description FROM artifacts WHERE museum_id = '<id>' LIMIT 5;"
- For browsing: run \\`yarn db:studio\\` to open Prisma Studio at http://localhost:5555
- The DATABASE_URL environment variable is in .env (never commit or log it)
- All production data access must be read-only during research steps. Write operations only during implementation.

---

#### Cycle Step 1 -- RESEARCH

GOAL: Understand the Belvedere collection and prepare the pipeline for a paintings-focused Standard run.

Create an agent team of 3 teammates using Sonnet:

1. **Database Investigator** -- Check if Belvedere already exists in the database (\\`SELECT * FROM museums WHERE name ILIKE '%belvedere%'\\`). If it exists, assess what data is there (pipeline status, artifact count, mode). Check if a re-run or fresh run is appropriate. Also check current system configuration: what model registry settings are active? Are there any pipeline jobs currently running?

2. **Belvedere Collection Researcher** -- Research the Belvedere painting collection using web search. Identify: key works (The Kiss, Judith, etc.), periods represented, approximate number of notable paintings (for target piece count estimation). Also check if the Belvedere has multiple buildings (Upper/Lower Belvedere, 21er Haus) and whether "paintings only" needs further scoping.

3. **Pipeline Configuration Analyst** -- Read the pipeline intake code (`src/pipeline/stages/00-intake.ts`, `src/lib/prompts/intake.ts`) and the re-run code (`src/pipeline/stages/00c-rerun-intake.ts`). Determine: how to scope to "paintings only" (via `specialInstructions` parameter? Does the intake prompt support collection filtering?). Review the API endpoint for triggering runs (`src/app/api/museums/[id]/route.ts` or the dashboard). Estimate Standard-mode cost and duration.

DELIVERABLES:
- Consolidated summary: (a) Belvedere DB status, (b) collection overview with target piece count recommendation, (c) pipeline configuration for paintings-only Standard run, (d) cost/time estimate
- Save as \\`docs/dev-specs/<YYYYMMDD>_BELVEDERE_V3_RUN_PREP.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407)

---

#### Cycle Step 2 -- PLAN

Based on the research, define the complete Belvedere run configuration and validation protocol.

Create the plan as \\`docs/dev-specs/<YYYYMMDD>_BELVEDERE_V3_RUN_PLAN.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407).

INCLUDE:
1. **Run configuration:** museum name, pipeline mode (Standard), target piece count, special instructions text (paintings only, scoping details), target languages (recommend EN + DE since it's Vienna -- Hermann decides)
2. **Quality checklist:** for each artifact, what does "good V3 output" look like? List specific checks.
3. **User testing protocol:** Minimum 5 visitor personas to test:
   1. Casual tourist (English, time-constrained, "what should I see?")
   2. Art history enthusiast (deep knowledge, expert vocabulary)
   3. Child-friendly mode (parent asking on behalf of a child)
   4. Couple on a date (romantic context, shared exploration)
   5. Quiet reflective visitor (minimal speech, long pauses, emotionally engaged)
   Optional additional personas (if time permits): 6. German-speaking visitor (if DE language is included -- test translation voice quality), 7. Rushed visitor who warms up mid-visit (test course correction).
   What scenarios to run, what to evaluate, how to record feedback.

   **Evidence-based test scenarios (from user testing -- test ALL of these):**

   1. **The "stop and go" visitor:** Tester says "stop" after every response and rapidly asks about new artworks. Henry must respond with under 60 words and NOT offer "would you like more" after every turn. (Tests: first-response cap, Open Door frequency, stop compliance)

   2. **The "what am I looking at" visitor:** Tester points at a figure/detail and asks Henry to identify it ("Who is that woman?" / "Which one is Martha?"). Henry must give identification first, not atmosphere. (Tests: request-type matching)

   3. **The correction recovery:** Tester deliberately names the wrong painting, then corrects Henry. Henry must pivot without over-apologizing or losing momentum. (Tests: artwork stickiness, graceful recovery)

   4. **The deepening thread:** Tester asks 5+ follow-up questions on one artwork, going from visual to biographical to technical. Henry must follow the thread without resetting to visual guidance each time. (Tests: progressive profiling, depth adaptation)

   5. **The silent browser:** Tester says nothing for 30+ seconds between questions. Henry must not fill the silence or offer "would you like more." (Tests: patience invariant, silence-as-positive-act)

   6. **The young casual visitor:** Tester uses simple vocabulary and very short questions ("Who is Klimt?" / "What's this?"). Henry must not respond with literary language or 150-word narratives. (Tests: vocabulary adaptation, pacing adaptation)

   7. **The practical question mid-tour:** Tester asks about opening hours, cafe location, or room navigation in the middle of an art discussion. Henry must answer directly without pivoting back to art content. (Tests: request-type matching, operational data)

4. **Success/failure criteria:** what constitutes a PASS vs. FAIL for the entire run
5. **Iteration plan:** if specific artifacts fail quality, which phase to loop back to (prompt issue -> Phase 1, content issue -> Phase 2, pipeline issue -> fix here)

Hermann reviews and decides on target languages before the run starts.

---

#### Cycle Step 3 -- IMPLEMENT

GOAL: Execute the Belvedere Standard pipeline run and deploy the agent.

Create an agent team of 2:

1. **Run Operator** -- Trigger the Belvedere pipeline run via the dashboard or API with the approved configuration. Monitor the run through all stages: INTAKE, SOURCE_DISCOVERY, DEEP_RESEARCH, COPYRIGHT_CHECK, CONTENT_WRITE, QUALITY_ASSURANCE, DATA_STRUCTURE, ELEVENLABS_DEPLOY, TRANSLATION (if DE included). Report progress at each stage transition. If any stage fails, investigate the error and report immediately. Use the pipeline status queries from CLAUDE.md to monitor.

2. **Output Inspector** -- As soon as CONTENT_WRITE completes, begin reviewing artifact content. Don't wait for the full pipeline -- start assessing quality in parallel. Read 10+ artifact `contentMarkdown` fields from the database. Check each against the 6 narrative layers checklist. Flag any artifacts that are missing layers or that sound clinical/generic rather than warm/Henry-like. Also review the museum overview content for a strong Henry opening.

RULES:
- Do NOT modify pipeline code during the run. If there's a bug, document it and fix after the run.
- If the run fails mid-pipeline, capture the error, check orphan status, and report before re-attempting.

DELIVERABLE: Belvedere agent deployed on ElevenLabs. Output Inspector's quality report on 10+ artifacts. Any issues documented.

---

#### Cycle Step 4 -- VALIDATE

GOAL: Comprehensive validation of the Belvedere V3 agent -- both automated quality checks and preparation for Hermann's user testing.

Create an agent team of 2:

1. **Content Quality Auditor** -- Systematic review of ALL Belvedere artifacts (not just a sample):
   - For each artifact: score the 6 narrative layers as present/partial/missing
   - Check for Henry voice quality: warmth, sensory language, story arcs, no clinical/textbook tone
   - Verify the museum overview provides a strong opening for Henry's greeting
   - Check for factual consistency: do discovery connections reference real relationships between artworks?
   - Produce a scorecard: % of artifacts with all 6 layers, % with Henry-quality voice, list of weakest artifacts

2. **Agent Functionality Tester** -- Test the deployed ElevenLabs agent:

   **Agent verification must be API-based, not voice-call-based:**
   - Verify agent exists: \\`curl -H "xi-api-key: $ELEVENLABS_API_KEY" "https://api.elevenlabs.io/v1/convai/agents/<AGENT_ID>"\\`
   - Verify V3 system prompt is active: check \\`conversation_config.agent.prompt.prompt\\` field in the API response
   - Verify KB documents uploaded: check \\`conversation_config.agent.prompt.knowledge_base\\` field
   - Verify turn_timeout is -1: check \\`conversation_config.turn.turn_timeout\\` field (per CLAUDE.md critical rules)
   - Verify skip_turn tool is enabled: check \\`conversation_config.agent.prompt.tools\\` field
   - Content tool test: This can only be tested via an actual conversation (voice or widget). The Agent Functionality Tester should initiate one test conversation and verify the content tool returns artifact data.
   - Verify operational data (hours, tickets) is accessible if present

   If DE language is included in the Belvedere run: test a complete German conversation flow. Verify that Henry's warmth, guided seeing language, and storytelling voice survive translation. Specifically check: (a) does German Henry still use sensory directional language? ("Schauen Sie auf die Hande..."), (b) does he maintain conversational warmth or shift to formal/stiff German?, (c) are thought seeds and observational nudges natural in German? This is critical because the translation engine in \\`src/pipeline/translation.ts\\` uses Claude Sonnet -- the translation prompt must produce Henry-quality German, not textbook German.

DELIVERABLE: Scorecard + functionality report. Issues categorized as: prompt-level (fix in Phase 1 loop), content-level (fix in Phase 2 loop), or pipeline-level (fix here).

AFTER VALIDATION: Hermann conducts user testing across 5+ visitor personas. Results determine whether to proceed to Phase 4 or iterate.

---

## Phase 4: Codify the V3 Standard

**Goal:** Lock in the V3 system as the production default, ensuring all future museum runs automatically use V3 prompts.

**Why before migration:** Before touching 28 existing museums, we need to be confident that V3 is the default going forward. This phase also handles any small refinements from the Belvedere testing.

### Research
- Catalog all files that reference the system prompt, content prompts, or voice criteria
- Check if any hardcoded V2 assumptions exist in the pipeline (QA stage voice scoring, content rewrite prompts, etc.)
- Review the QA stage (`05-quality-assurance.ts`) to ensure its quality gates align with V3 criteria

### Planning
- List every file that needs updating to align with V3
- Define updated QA voice quality criteria that match Henry V3's adaptive personality
- Plan any prompt version management (do we keep V2 accessible for reference?)

### Implementation
- Apply any refinements from Belvedere testing to the V3 system prompt and content prompts
- Update QA stage voice quality criteria
- Update any remaining pipeline prompts that reference the old voice style
- Ensure V3 is the default for all new pipeline runs
- Archive V2 prompts in the wiki (move to a "V2 -- Legacy" folder or archive)

### Validation
- Run a Light-mode pipeline for a small museum to verify the full V3 pipeline works end-to-end without manual intervention
- Verify QA stage passes with V3 content
- Verify no V2 remnants remain in the active prompt path

**Exit criteria:** All new museum runs automatically produce V3-quality content with the adaptive Henry personality. QA gates aligned. V2 prompts archived.

### Execution Prompt

> **Copy and execute this complete prompt to run Phase 4. All 4 cycle steps are included.**

---

**CONTEXT:** Belvedere V3 has passed validation and Hermann's user testing (Phase 3 done). The V3 system is proven. Now we need to lock it in as the production default so all future museum runs automatically use V3 -- and clean up any V2 remnants.

**Design anchor:** Every implementation decision in this phase must be evaluated against the Adaptive Personality System design document (\\`wiki/strategy/20260320-henrys-adaptive-personality-system.html\\`). This document defines the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, adaptation boundaries, and the Identity Test. If any implementation choice conflicts with the design doc, the design doc wins. The design doc is the "idea." This roadmap is the "how." The founding vision (\\`wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html\\`) provides the emotional truth behind the design.

---

#### Cycle Step 1 -- RESEARCH

GOAL: Find every file in the codebase that references the old V2 voice style, prompt assumptions, or QA criteria that need updating for V3.

Create an agent team of 2 teammates using Sonnet:

1. **Codebase Scanner** -- Explicitly scan these files for V2 remnants: \\`src/lib/prompts/agent-personality.ts\\`, \\`src/lib/prompts/content.ts\\`, \\`src/lib/prompts/rewrite.ts\\`, \\`src/lib/prompts/voice-optimize.ts\\`, \\`src/pipeline/stages/05-quality-assurance.ts\\` (voice quality gate), \\`src/pipeline/stages/04-content-write.ts\\` (anti-meta fallback text). Also grep the entire codebase for: (a) references to the agent personality prompt or voice criteria, (b) content rewrite prompts that enforce a voice style, (c) any hardcoded strings like "world-leading expert" or other V2 phrases that were replaced in V3, (d) CLAUDE.md references to prompt versions.

   **Known files containing Henry voice/personality instructions (verify each, search for others):**

   | File | What it contains | V3 scope |
   |------|-----------------|----------|
   | \\`src/lib/prompts/agent-personality.ts\\` | ElevenLabs agent system prompt | Phase 1 (primary target) |
   | \\`src/lib/prompts/content.ts\\` | Content-write system prompt + all 4 entity prompts | Phase 2 (primary target) |
   | \\`src/lib/prompts/rewrite.ts\\` | Content generation prompt + voice optimization prompt | Phase 2 (must update) |
   | \\`src/lib/prompts/voice-optimize.ts\\` | Conversational quality check scoring criteria | Phase 4 (must align) |
   | \\`src/pipeline/stages/05-quality-assurance.ts\\` | Voice quality gate (imports from voice-optimize.ts) | Phase 4 (must align) |
   | \\`src/pipeline/stages/04-content-write.ts\\` | Anti-meta fallback text (line ~856) | Phase 4 (check V2 remnants) |
   | \\`src/lib/prompts/intake.ts\\` | Intake planning prompt (may reference voice style) | Phase 2 (check) |
   | \\`src/lib/prompts/discovery.ts\\` | Discovery synthesis prompt (may reference voice style) | Phase 4 (check) |

   Scan ALL files in \\`src/lib/prompts/\\` and grep for: "Henry", "warm", "grandfather", "companion", "guided seeing", "observational nudge", "thought seed", "museum companion", "world-leading expert" (V2 remnant).

   Produce a complete inventory of every file that touches Henry's voice or personality.

2. **QA Alignment Analyst** -- Deep-read both the QA stage implementation (\\`src/pipeline/stages/05-quality-assurance.ts\\`) AND the voice quality prompt template (\\`src/lib/prompts/voice-optimize.ts\\`). The QA stage imports \\`CONVERSATIONAL_QUALITY_CHECK\\` from \\`voice-optimize.ts\\` (line 21 of the QA stage file). This template defines the scoring criteria (rhythm, length, engagement, accessibility, flow, guidedSeeing, discoveryEngagement). If V3 adds new quality dimensions (e.g., adaptive tone, invariant presence, anti-detection compliance), they must be added BOTH to this template AND to the QA stage's interpretation of the scores. Understand exactly what voice quality criteria are currently checked. Compare against V3 requirements (9 invariants, adaptive dimensions). Identify specific QA criteria that need updating.

DELIVERABLES:
- Complete file inventory of V2 references
- QA gap analysis: current criteria vs. V3 criteria
- Save as \\`docs/dev-specs/<YYYYMMDD>_V3_CODIFICATION_RESEARCH.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407)

---

#### Cycle Step 2 -- PLAN

Based on the research, write the V3 codification plan.

Create as \\`docs/dev-specs/<YYYYMMDD>_V3_CODIFICATION_PLAN.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407).

STRUCTURE:
1. For each file that needs updating: exact change description, before/after
2. Updated QA voice quality criteria (the specific checklist the QA stage should evaluate)
3. V2 prompt archival plan: which wiki entries to archive, what to preserve for reference
4. Verification: a Light-mode test run on a small museum to prove the full V3 pipeline works
5. Files NOT to touch: pipeline infrastructure, database schema, ElevenLabs integration

Risk areas: #1 QA criteria too strict causing false failures on V3 content. #2 Missed V2 reference causing inconsistent behavior.

---

#### Cycle Step 3 -- IMPLEMENT

GOAL: Apply all V3 codification changes and archive V2.

Create an agent team of 3:

1. **Code Updater** -- Apply all changes from the plan: update QA voice criteria, update any remaining prompt references, update CLAUDE.md documentation. Each change is small and targeted -- follow the file inventory exactly.

2. **Architect Overseer** -- Review every change. Verify: (a) QA criteria are achievable (not so strict that good V3 content fails), (b) no pipeline infrastructure was accidentally modified, (c) all V2 references are gone from the active code path, (d) CLAUDE.md accurately reflects V3.

3. **Wiki Archiver** -- Archive the V2 prompt entries in the wiki (use `/api/archive` endpoint). Verify V3 prompt entries are complete and current.

DELIVERABLE: All V3 changes committed. V2 archived. Architect confirms system integrity.

---

#### Cycle Step 4 -- VALIDATE

GOAL: Prove the full V3 pipeline works end-to-end with no manual intervention.

Create an agent team of 2:

1. **Pipeline Validator** -- Trigger a Light-mode test run for a small museum (pick one that's quick to process or use a museum that can be re-run). Monitor all stages. Verify: (a) content-write produces V3-quality output with narrative layers, (b) QA stage passes without false failures, (c) ElevenLabs agent deploys with V3 system prompt, (d) the entire pipeline completes successfully.

2. **Codebase Auditor** -- Final sweep: grep for any remaining V2 patterns, verify no debug code was left, verify CLAUDE.md is consistent, verify wiki state (V3 entries active, V2 entries archived). Check git diff to ensure only intended files were modified.

DELIVERABLE: Structured pass/fail. The test run is the ultimate proof -- if a museum goes through the full pipeline and comes out with V3-quality Henry, this phase is done.

---

## Phase 5: Existing Museum Migration Strategy

**Goal:** Research and decide the migration strategy for the 28 existing museums, then execute it.

**Why last:** This is the highest-risk, highest-cost phase. It touches production content that real users interact with. The V3 system must be proven on Belvedere and codified as default before we touch existing data.

**This phase is deliberately structured as a research-first decision** because the right approach depends on factors that require investigation:

### Research

This is the most important step of Phase 5. The team must answer these questions:

**Question 1: Re-run from scratch vs. build on existing data?**
- How much of each museum's existing KB content already meets V3 quality?
- If we re-run from scratch, what do we lose? (Custom edits, manual fixes, hand-tuned content)
- If we build on existing data, can we add the missing narrative layers (visual journeys, hooks, deep threads) without re-running the full pipeline? Could a targeted content-rewrite pass add V3 layers to existing content?
- What is the cost difference? (Full re-run = ~$10-15/museum; targeted rewrite = potentially less)
- What is the time difference? (Full re-run = ~2-3 hours/museum; targeted rewrite = potentially faster)

**Question 2: Batch strategy**
- Should all 28 museums be migrated at once, or in batches?
- Which museums are highest-priority for migration? (Most-visited? Most content? Upcoming partnerships?)
- Can migrations run in parallel, and how many concurrent runs can the infrastructure handle?

**Question 3: Agent continuity**
- Re-runs use atomic KB swap (agent ID unchanged). Does this affect visitor experience during migration?
- Should we migrate during low-traffic hours?
- Do we need a rollback plan if V3 content degrades a specific museum?

**Question 4: Translation impact**
- Existing museums have multi-language agents. Re-running means re-translating everything.
- Is there a way to preserve existing translations for content that hasn't changed?
- Cost implications of re-translating 28 museums x up to 5 languages

### Planning

Based on the research findings, produce a concrete migration plan:

- **Decision:** Full re-run vs. targeted rewrite vs. hybrid (per-museum decision based on content quality assessment)
- **Batch schedule:** Which museums in which order, how many in parallel
- **Cost estimate:** Total API costs for the chosen approach
- **Timeline:** Calendar estimate with milestones
- **Rollback strategy:** How to revert a museum if V3 content is worse than V2
- **Hermann approval required** before any existing museum is modified

### Implementation

- Execute the migration plan batch by batch
- Monitor each batch for quality and errors
- Apply the V3 system prompt to all migrated agents
- Re-translate where needed

### Validation

- Spot-check 3-5 artifacts per migrated museum for V3 narrative layer completeness
- Verify all ElevenLabs agents are live and functional post-migration
- Compare pre-migration and post-migration content for any regressions
- Hermann tests 2-3 migrated museums with different visitor personas
- Monitor for any user-facing issues in the week following each batch

**Exit criteria:** All 28 museums running V3 content with the adaptive Henry personality. No quality regressions. All agents live and functional across all languages.

### Execution Prompt

> **Copy and execute this complete prompt to run Phase 5. All 4 cycle steps are included.**

---

**CONTEXT:** V3 is the production default (Phase 4 done). All new museums run with V3 automatically. Now the question: what about the 28 existing museums running V2 content? This phase is deliberately research-first because the right migration strategy (re-run from scratch vs. targeted rewrite vs. hybrid) depends on analysis that hasn't been done yet.

The stakes are high: these museums have live ElevenLabs agents that real users interact with. Any migration must not degrade the experience.

**Design anchor:** Every implementation decision in this phase must be evaluated against the Adaptive Personality System design document (\\`wiki/strategy/20260320-henrys-adaptive-personality-system.html\\`). This document defines the 9 invariants, 6 adaptive dimensions, progressive visitor profiling model, adaptation boundaries, and the Identity Test. If any implementation choice conflicts with the design doc, the design doc wins. The design doc is the "idea." This roadmap is the "how." The founding vision (\\`wiki/strategy/20260320-henry-vision-the-soul-of-aitourpilot.html\\`) provides the emotional truth behind the design.

DATABASE ACCESS:
- For read-only queries: use \\`psql $DATABASE_URL\\` with the queries from CLAUDE.md
- Example: psql $DATABASE_URL -c "SELECT name, description FROM artifacts WHERE museum_id = '<id>' LIMIT 5;"
- For browsing: run \\`yarn db:studio\\` to open Prisma Studio at http://localhost:5555
- The DATABASE_URL environment variable is in .env (never commit or log it)
- All production data access must be read-only during research steps. Write operations only during implementation.

---

#### Cycle Step 1 -- RESEARCH

GOAL: Answer the four key questions that determine migration strategy. This is the most important cycle step of Phase 5 -- the decision that follows depends entirely on what we find here.

Create an agent team of 4 teammates using Sonnet:

1. **Content Quality Auditor** -- Sample 3-5 artifacts from each of 5 diverse museums (mix of Light/Standard/Full modes). Read the `contentMarkdown` and assess: how much already meets V3 quality? Score each against the 6 narrative layers. Categorize museums into tiers: (a) already close to V3 (just needs system prompt swap), (b) needs targeted content enrichment, (c) needs full re-run. This directly answers Question 1.

2. **Cost & Infrastructure Analyst** -- Reference the existing cost analysis at \\`docs/reference/20260216_COST_ANALYSIS_AND_MODEL_SELECTION.md\\` for per-museum API cost baselines. The CLAUDE.md documents LLM model routing: content writing uses Claude Sonnet 4.5, fact extraction uses Claude Haiku 4.5. Standard mode targets ~300,000 chars output. Use these baselines to estimate re-run costs per museum per mode. Calculate: (a) cost of re-running all 28 museums (API costs per mode, total), (b) cost of a targeted rewrite pass (if feasible -- estimate LLM calls needed), (c) translation costs for re-translating 28 museums x N languages, (d) infrastructure capacity -- how many parallel runs can the Render worker + Supabase handle? (e) time estimate for each approach. Check current Upstash/Supabase usage to ensure headroom.

3. **Translation Impact Researcher** -- Investigate: (a) how the translation stage works (`src/pipeline/translation.ts`), (b) whether a re-run preserves any translation work or re-translates everything, (c) the atomic KB swap mechanism -- is there any visitor-facing downtime during migration? (d) whether we can selectively re-translate only changed content (or is it all-or-nothing?). This answers Questions 3 and 4.

4. **Migration Architect** -- Synthesizes findings from all teammates. Also investigates: (a) does the re-run pipeline (`00c-rerun-intake.ts`) support a "content-only" re-run that skips research stages if existing research data is good? (b) what is the rollback mechanism if V3 content is worse for a specific museum? (c) can we batch museums by priority (partnership museums first)? Produce the final recommendation.

DELIVERABLES:
- Each teammate sends findings to the Migration Architect
- The Migration Architect produces a consolidated decision document: (a) per-museum quality tier assessment, (b) cost comparison table (re-run vs. rewrite vs. hybrid), (c) recommended strategy with rationale, (d) batch schedule proposal, (e) rollback plan, (f) translation handling
- Save as \\`docs/dev-specs/<YYYYMMDD>_MUSEUM_MIGRATION_V3_RESEARCH.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407)

COORDINATION: The Content Quality Auditor's tier assessment directly feeds the Migration Architect's strategy. The Cost Analyst's numbers constrain what's feasible. Share findings as they emerge, don't wait until the end.

**Hermann reviews and approves the migration strategy before any museum is touched.**

---

#### Cycle Step 2 -- PLAN

Based on the approved migration strategy, write the execution plan.

Create as \\`docs/dev-specs/<YYYYMMDD>_MUSEUM_MIGRATION_V3_PLAN.md\\` (replace <YYYYMMDD> with today's date, e.g., 20260407).

STRUCTURE:
1. **Migration approach per museum** -- table: museum name, current mode, quality tier, action (re-run / rewrite / prompt-swap-only), target languages, estimated cost, estimated time
2. **Batch schedule** -- which museums in which batch, how many in parallel, calendar timeline
3. **Pre-migration checklist** per batch -- what to verify before starting

**Pre-migration backup (MANDATORY):**
Before the first batch begins, verify that Supabase automated backups are enabled and take a manual snapshot:
- Supabase dashboard > Database > Backups > verify daily PITR is active
- Take a manual backup before the first migration batch
- Record the backup timestamp in the migration plan
- For each batch: note the "last known good" timestamp so PITR can restore to pre-batch state if needed

If Supabase backup is not available or PITR is not active, do NOT proceed with migration until this is resolved.
4. **Rollback procedure** -- step-by-step: how to revert a museum's KB and system prompt if V3 content is worse. Include the specific API calls or pipeline commands.
5. **Monitoring plan** -- what to check after each batch (agent functionality, content quality, user-facing issues)
6. **Translation handling** -- which museums need re-translation, estimated cost, parallel vs. sequential
7. **Total cost and timeline** -- budget for the entire migration

Hermann approves the plan and batch schedule before execution begins.

---

#### Cycle Step 3 -- IMPLEMENT

GOAL: Execute the migration batch by batch.

Create an agent team of 3:

1. **Migration Operator** -- Execute each batch following the plan. For each museum: (a) trigger the appropriate action (re-run, rewrite, or prompt-swap), (b) monitor pipeline progress, (c) verify completion, (d) trigger translation if needed. Report status after each museum completes. If any museum fails, stop the batch and report.

   **SCOPE CONTROL:** Phase 5 is a MIGRATION phase, not a development phase. The Migration Operator must NOT write new pipeline code, modify existing stage implementations, or change database schema. The only allowed actions are: (a) triggering re-runs via existing API endpoints, (b) monitoring pipeline status via existing queries, (c) updating system prompt text via existing deployment mechanisms. If a bug is discovered during migration, STOP and document it. Do not fix infrastructure during a migration.

2. **Quality Spot-Checker** -- As each museum completes, immediately sample 3-5 artifacts and verify V3 narrative layer quality. Compare against the pre-migration content. Flag any regressions. This is a rapid quality gate -- not a full audit, but enough to catch obvious problems before the batch continues.

3. **Architect Overseer** -- Monitors the overall migration. Tracks: (a) which museums are done, in progress, or pending, (b) any issues or anomalies, (c) cost burn rate vs. budget, (d) whether the batch schedule needs adjustment. If the Quality Spot-Checker flags regressions, the Architect decides: pause batch, investigate, or proceed.

RULES:
- Hermann must approve each batch before it starts (first batch approval covers the full plan, subsequent batches proceed unless Hermann pauses)
- If 2+ museums in a batch show quality regressions, STOP and investigate before continuing
- Do not rush. A museum that runs correctly once is better than three that need re-runs.

DELIVERABLE: All batches executed. Spot-check reports per museum. Migration status tracker updated.

---

#### Cycle Step 4 -- VALIDATE

GOAL: Final validation that all 28 museums are live, functional, and running V3-quality content.

Create an agent team of 3:

1. **Agent Health Checker** -- Verify every ElevenLabs agent across all museums and languages: (a) agent is live and responding, (b) V3 system prompt is active, (c) KB documents are uploaded and current, (d) operational data is accessible, (e) turn_timeout is -1. Produce a health report: museum x language matrix with pass/fail per cell.

2. **Content Quality Auditor** -- Deep-sample 3-5 artifacts from each of 5 migrated museums (different tiers). Full 6-layer assessment. Compare pre-migration vs. post-migration content. Flag any regressions. Produce a quality scorecard.

3. **Regression Monitor** -- Check for any user-facing issues in the week following migration: (a) are there error reports? (b) are conversation logs showing problems? (c) are any agents unresponsive? (d) has anything degraded on the public API (\\`GET /api/public/museums\\`)? Monitor the public API (\\`GET /api/public/museums\\`) during and after each migration batch. Verify: (a) all museums are still listed, (b) all language variants have valid agent IDs, (c) response times are stable (no degradation from concurrent re-runs), (d) no museums show error states in the response. Run this check before each batch, immediately after each batch, and daily for one week after the final batch.

DELIVERABLE: Each validator produces a structured verdict (PASS/FAIL). All 28 museums must pass health checks. Quality scorecard must show no regressions. If issues surface during the monitoring week, they are addressed before the migration is marked complete.

AFTER VALIDATION: The Henry V3 Adaptive Personality migration is complete. All museums -- existing and future -- run with V3. Document lessons learned for future large-scale migrations.

---

## Phase Dependencies & Timeline

```
Phase 1: V3 System Prompt
    |
    v
Phase 2: Content Pipeline Enrichment
    |
    v
Phase 3: Belvedere Validation Run
    |         ^
    v         | (iterate if needed)
    +---------+
    |
    v
Phase 4: Codify V3 Standard
    |
    v
Phase 5: Existing Museum Migration
```

| Phase | Estimated effort | Depends on |
|-------|-----------------|------------|
| 1. V3 System Prompt | 1 session | -- |
| 2. Content Pipeline Enrichment | 1-2 sessions | Phase 1 |
| 3. Belvedere Validation Run | 1 session (run) + testing time | Phase 1 + 2 |
| 4. Codify V3 Standard | 1 session | Phase 3 validated |
| 5. Existing Museum Migration | 2-4 sessions (research-heavy) | Phase 4 |

Phases 1-4 can realistically be completed in a focused week. Phase 5 depends on the research findings and the chosen migration strategy -- it could take 1-3 weeks depending on scope.

---

## Key Decisions That Remain Open

These decisions will be made during execution, not upfront:

| Decision | When it's made | Who decides |
|----------|---------------|-------------|
| V3 prompt final wording | Phase 1 validation | Hermann |
| Whether intake prompts need changes | Phase 2 research | Agent team |
| Belvedere target languages (EN-only vs EN+DE) | Phase 3 planning | Hermann |
| Number of Belvedere test pieces | Phase 3 planning | Agent team + Hermann |
| Full re-run vs. targeted rewrite for existing museums | Phase 5 research | Hermann (with agent team recommendation) |
| Migration batch order and parallelism | Phase 5 planning | Agent team + Hermann |
| Rollback criteria | Phase 5 planning | Hermann |

---

*This roadmap is a companion to the [Henry Adaptive Personality System](20260320-henrys-adaptive-personality-system.html) design doc and the [Henry Vision](20260320-henry-vision-the-soul-of-aitourpilot.html) founding document. The design defines WHAT Henry becomes. This roadmap defines HOW we get there.*
