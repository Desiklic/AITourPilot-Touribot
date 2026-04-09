# 20260408-museum-deep-research-know-before-you-run

*Source: Business Wiki / upcoming-features/20260408-museum-deep-research-know-before-you-run.html*

## The Gap

Today, when you add a new museum to the content factory, you fill in a name, city, type, mode, and optionally Special Instructions. Then you press "Create Museum & Start Pipeline" and hope the intake LLM figures out what matters.

For art museums like Belvedere, this works well -- the pipeline knows how to research paintings, artists, and galleries. But for Bletchley Park? The pipeline doesn't know that:
- This is a WWII codebreaking site, not an art museum
- The "artifacts" are machines (Enigma, Bombe, Colossus), not paintings
- The emotional core is people (Alan Turing, Dilly Knox, the Wrens), not artists
- The visitor experience is site-based -- walking between huts, each a chapter of a story
- "Guided seeing" becomes "guided imagining" for events that happened in these rooms
- There are possibly fewer physical artifacts but vastly more historical narrative

Without this context, the intake LLM makes generic assumptions. It might select 80 "artifacts" that are mostly room descriptions instead of focusing on the machines, the people, and the pivotal moments. The Special Instructions field can fix this -- but only if you know what to write.

**The insight: the pipeline needs a research phase BEFORE the pipeline.**

---

## The Feature: Museum Deep Research

A new capability in the content factory that researches a museum thoroughly before the pipeline runs, producing:

1. **Museum Intelligence Report** -- what this museum is about, what makes it unique, what visitors come to see, what the emotional core is
2. **Recommended Pipeline Configuration** -- mode, piece count, type/subtype, target languages
3. **Draft Special Instructions** -- ready to paste into the pipeline, tuned to this specific museum
4. **Key People & Stories** -- who matters, what happened here, what narrative threads to follow
5. **Content Strategy** -- should Henry focus on visual guidance (art museums), historical narrative (heritage sites), scientific explanation (science museums), or immersive storytelling (archaeological sites)?

### Two Examples

**Belvedere (art museum):** The research would have told us: "101 paintings across Medieval to contemporary. Core: 24 Klimt paintings including The Kiss and Judith. Strong Schiele representation. Upper Belvedere permanent collection only. PAINTINGS ONLY -- exclude decorative arts, sculpture, architecture." We wrote this manually for the Special Instructions. The feature would generate it automatically.

**Bletchley Park (heritage site):** The research would tell us: "WWII codebreaking headquarters. Not artifact-centric -- the experience is about what HAPPENED here. Key machines: Enigma, Bombe, Colossus. Key people: Alan Turing, Dilly Knox, Gordon Welchman, the Wrens. Key locations: Hut 8 (Naval Enigma), Hut 6 (Army/Air Force), Hut 3 (Intelligence), Block B (Bombe room). The narrative is chronological: from pre-war preparation through Enigma breaking to D-Day intelligence. Henry should focus on storytelling and historical imagination, not visual description of objects. Recommended: STANDARD, 80 items, mix of machines (20), people (15), locations/huts (15), key events/stories (30)."

That Special Instructions text would transform the pipeline run from generic to precisely targeted.

---

## How It Works

### Option A: Button in the UI (lightweight)

Add a **"Research First"** button next to "Create Museum & Start Pipeline" on the Add Museum page. It takes the museum name + city + type and runs a single deep research call, then displays results in a panel. The operator reviews, edits, and the Special Instructions are auto-filled.

### Option B: Dedicated Research Engine (recommended)

Integrate with **FelixBot's deep research framework** (`~/FelixBot/tools/executors/research.py`). FelixBot has a production-grade multi-pass research system that produces 3,000-5,000+ word reports using **Gemini** (the best and most cost-effective model for deep research). The key components:

- **Research Planner** -- decomposes a museum research task into targeted queries
- **Research Runner** -- executes parallel web searches and data gathering
- **Research Synthesizer** -- produces a structured, publication-quality report
- **Deep Research mode** -- extended analysis that covers every relevant dimension

The Gemini API key is already available in the content-factory (`GOOGLE_AI_API_KEY` in .env). The latest Gemini model should be used for maximum quality and cost-effectiveness.

**The vision:** Type "Bletchley Park, Milton Keynes" --> click "Research" --> wait 60 seconds --> receive a comprehensive museum intelligence report + draft Special Instructions + recommended pipeline config. Review, adjust, run.

---

## Special Instructions: Does It Actually Work?

**Yes.** The Special Instructions field is injected into the intake prompt with this framing:

> **You MUST follow these instructions when building the Research Plan. They override any default assumptions.**

This is a hard override -- the intake LLM treats Special Instructions as mandatory constraints when selecting artifacts and planning research. The Belvedere run proved this: "PAINTINGS ONLY" resulted in 101 paintings and zero sculptures/decorative arts, exactly as instructed.

**But there are limits:**
- Special Instructions only affect **Stage 0 (Intake)** -- the research plan. They don't directly control what Stage 2 (Deep Research) discovers or what Stage 4 (Content Write) produces.
- If Special Instructions say "focus on people" but the intake selects only artifacts, the downstream stages won't compensate.
- The quality of the pipeline output is directly proportional to the quality of the Special Instructions.

This is exactly why the Deep Research feature matters: **better input = better output, for every subsequent stage.**

---

## What This Enables

- **Non-art museums done right:** Heritage sites, science museums, archaeological collections, architectural landmarks -- each gets a tailored pipeline configuration
- **Faster operator workflow:** No more googling "what is Bletchley Park famous for" before starting a pipeline
- **Consistent quality:** Every museum gets researched to the same depth, regardless of the operator's domain knowledge
- **Scalable to 100+ museums:** The research step takes 60 seconds and costs ~$0.05-0.10. Negligible at scale.

---

## Integration with Phase 2

This feature slots naturally into the Phase 2 scaling roadmap:

- **Phase 6b (Open API Integration)** -- the research step could identify which public APIs (Europeana, Smithsonian, etc.) have data for this specific museum, and include API source recommendations in the Special Instructions
- **Phase 8 (Content Optimization Flywheel)** -- after 50+ conversations at a museum, the flywheel data could auto-update the Special Instructions with insights like "visitors consistently ask about X -- ensure it's covered"

---

## Next Steps

1. Another agent will scope out the detailed implementation -- integrating FelixBot's Gemini-powered deep research with the content factory's Add Museum workflow
2. For Bletchley Park NOW: the research is being done manually by a dedicated agent, and results will go into Special Instructions for the V3 Standard run
