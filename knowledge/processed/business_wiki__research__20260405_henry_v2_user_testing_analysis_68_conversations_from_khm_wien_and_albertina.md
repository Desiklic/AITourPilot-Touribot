# 20260405-henry-v2-user-testing-analysis-68-conversations-from-khm-wien-and-albertina

*Source: Business Wiki / research/20260405-henry-v2-user-testing-analysis-68-conversations-from-khm-wien-and-albertina.html*

# User Testing Analysis: 68 Conversations from KHM Wien and Albertina

**Date:** 5 April 2026
**Author:** Visitor Interaction Analyst (Claude)
**Data:** 68 real conversation transcripts from two museum testing sessions
**Purpose:** Evidence base for Henry V3 Adaptive Personality System implementation

---

## Executive Summary

Across 68 conversations (37 substantial, totalling ~4.5 hours of interaction), Henry V2 demonstrates genuine strengths in visual guidance and storytelling warmth, but suffers from a critical structural problem: **he consistently over-delivers on first response, forcing visitors to interrupt him or say "stop" repeatedly.** The data shows 56% of all agent responses were interrupted by the visitor, and users said "stop/stopp" 38 times across the dataset. Henry's average response is 84 words (within the 100-word target), but the distribution reveals that 33% of responses exceed 100 words and the *first response to a new artwork* is almost always in the 120-170 word range -- exactly where visitors lose patience.

The three tester profiles (Hermann, Simone, Mathias) reveal starkly different interaction patterns that V2 Henry fails to differentiate. V3's adaptive system is not a nice-to-have -- it is the minimum viable product for real visitors.

---

## 1. Conversation Pattern Analysis

### 1.1 How Visitors Open

The overwhelming pattern across all three testers is **"I'm standing in front of [artwork name]"** -- a direct, situational opening that announces location and requests content. This occurred in 17 of 37 substantial conversations.

**Common opener types:**

| Pattern | Example | Frequency |
|---------|---------|-----------|
| "I'm standing in front of X" | "Ich stehe gerade vor Peter Paulo Rubens Vincenzo il Gonzaga" (Conv 2) | ~46% |
| Direct question about artwork | "What is special about 'the kiss'" (Conv 59) | ~22% |
| General artist question | "Was kannst du mir uber Vermehr erzahlen?" (Conv 9) | ~11% |
| Practical question | "In welchem Teil des Gebaudes finde ich denn Vermeer?" (Conv 16) | ~5% |
| Continuing previous conversation | "Ja, bitte weiterreden" (Conv 3) | ~8% |
| Ambient/unintentional | Background noise, talking to companion (Conv 20) | ~8% |

**Key finding for V3:** Visitors almost always declare their physical location first. They rarely ask abstract questions. The system prompt should instruct Henry to treat every opening as "the visitor is standing in front of something right now" unless explicitly stated otherwise.

### 1.2 How Henry Responds (V2 Pattern)

Henry V2 has a consistent three-part response structure on first contact with a new artwork:

1. **Visual guidance opening** ("Schauen Sie zuerst auf..." / "Start with...")
2. **Interpretive middle** (story, context, emotional reading)
3. **Offer to continue** ("Wenn Sie mogen, erzahle ich Ihnen..." / "If you'd like...")

This structure works well intellectually but is **too long for first response**. Henry delivers 120-170 words before the visitor can react, creating a lecture dynamic rather than a conversation.

**Example -- Conv 1 (first response to Rubens question): 160 words, INTERRUPTED**

> "[ruhig] Sehr gern. Wenn Sie vor Rubens' Reuiger Magdalena mit Martha stehen, lassen Sie den Blick zuerst auf die Korperhalrung der Magdalena fallen: dieses leichte Nach-vorn-Sinken, als ware die ganze Figur ein einziges Eingestandnis. Rubens macht Reue nicht klein und nuchtern, sondern warm, menschlich, fast korperlich spurbar..."

The visitor interrupted -- they wanted to know which figure was Martha and which was Magdalena. Henry delivered atmosphere when the visitor needed identification.

### 1.3 Follow-Up Patterns

After Henry's first response, visitors show three distinct behaviors:

**Pattern A: Drilling deeper (Hermann-type)** -- Asks increasingly specific follow-up questions, stays on one artwork for 5-10 exchanges. Example from Conv 3 (Rubens, Wunder des Heiligen Franz Xaver):
- "Ja, bitte." (tell me the story)
- "Wie viele Leute haben beim Studio mitgemalt?" (how many studio assistants)
- "Wie wurden diese riesigen Bilder damals transportiert?" (transportation of large paintings)
- "Wie lange dauert das Ausharten der Farbe?" (how long does paint cure)

This visitor wants depth and follows threads to their logical conclusion. Henry handles this well.

**Pattern B: Quick-move (Simone-type)** -- Gets the essential information, says "Stopp", moves to next artwork. Rarely engages with Henry's offers to tell more. Example from Conv 6:
- User asks about specific painting
- Henry responds with 103 words
- "Okay, stopp. Stopp. Kannst du mir sagen, wer dieser Priester in der Bildmitte ist?"

This visitor treats Henry like a utility, not a companion. Henry's V2 response pattern frustrates them.

**Pattern C: Exploratory (Mathias-type)** -- Short questions, moves quickly between artworks, asks broad questions. Example from Conv 64:
- "Who is Albrecht Durer" (4 words)
- "The dead blue roller, can you tell me about that" (10 words)

This visitor is browsing. They want hooks, not deep dives. Henry's V2 responses are often too long and literary for this pattern.

### 1.4 Where Conversations Peak

The most engaged exchanges occur when:

1. **The visitor spots a detail and Henry confirms it.** Conv 9, the Vermeer map discussion: The user asks "Was ist denn das im Hintergrund auf dieser Tapete oder diesem Stoff?" -- Henry explains the wall map -- the visitor asks for "interesting details not many people know" -- Henry delivers the pinhole detail and hidden allegories. This is a five-exchange sequence of genuine discovery.

2. **The visitor asks a factual question and Henry wraps it in story.** Conv 8, Vermeer's children: "Wie viele Kinder hatte er?" / "Funfzehn Kinder. Vier starben jung..." The visitor is visibly shocked ("Was sagst du? Er hatte funfzehn Kinder...") and the conversation deepens into Vermeer's home life.

3. **The visitor corrects Henry and Henry recovers.** Conv 11, Cranach: The visitor says "Aber ich bin mehr interessiert daran, was mit diesen ganzen Hirschen in der Mitte passiert" -- Henry pivots immediately and the conversation becomes excellent.

### 1.5 Where Conversations Break Down

**Breakdown Type 1: "Stop" fatigue.** The visitor says "stop/stopp" multiple times because Henry keeps talking or because the system doesn't register the stop command quickly enough. Conv 5 contains 4 separate "stop" commands. Conv 6 has 5.

**Breakdown Type 2: Wrong artwork.** Henry confidently starts describing the wrong painting. Conv 4: User describes a figure in front of a Rubens painting. Henry says "Ich glaube, Sie stehen gerade vor Arcimboldo" -- completely wrong. The user must correct ("Nein, ich habe dir gerade gesagt, ich stehe vor Peter Paul Rubens...").

**Breakdown Type 3: ASR (speech recognition) failures.** The visitor's words are garbled by transcription, and Henry either misinterprets or asks for clarification in a way that breaks flow. Conv 1: User says something about their sister in school, Henry responds "da ist Ihnen der Satz ein wenig weggerutscht" -- technically correct but kills the conversation momentum.

**Breakdown Type 4: Henry talks into silence after being asked to stop.** The system sometimes generates two empty responses in a row (the skip_turn mechanism working) but then resumes talking unprompted. This is confusing for visitors.

---

## 2. Henry's V2 Strengths (What Already Works)

### 2.1 Visual Guidance Is Genuinely Excellent

Henry's "guided seeing" is the single strongest feature in V2, consistently present and often beautiful.

**Best example -- Conv 2, Theodor van Thulden's Heimsuchung:**

> "[slow] Gut, dann nehmen wir es wirklich wie eine Buhne, auf der sich ein leiser Moment gross anfuhlt. Im Kern ist es die Heimsuchung: Maria besucht ihre altere Verwandte Elisabeth, beide schwanger [...] Es ist eine Szene des Erkennens, aber nicht durch Worte, sondern durch Korper: das Innehalten, das Zueinander-Treten, diese kleine Spannung, bevor sich die Hande wirklich finden."

This is exactly what the V3 vision document describes: leading with seeing and feeling.

**Best example -- Conv 14, Bruegel's Jager im Schnee:**

> "Gehen Sie im Kopf an die untere linke Ecke: drei Jager stapfen heim, Schultern rund, die Hunde mager hinterher. Einer tragt als ganze Ausbeute nur einen kleinen Fuchs, fast beschamend wenig fur einen langen Tag."

The word "beschamend" (shamefully) is Henry at his best -- a single word that turns a visual description into an emotional experience.

### 2.2 Emotional Resonance When He Hits the Right Register

**Conv 8, Vermeer and his 15 children:**

> "Wenn man das im Hinterkopf hat, wirkt die Ruhe in der 'Malkunst' fast wie ein erkampfter Frieden, ein Raum aus Ordnung und Licht, den er sich inmitten eines lauten, vollen Haushalts innerlich gebaut hat."

This turns a biographical fact into a way of seeing the painting differently. The visitor was clearly affected.

**Conv 34, Vermeer -- the intimacy of looking over a painter's shoulder:**

> Visitor: "Was mich trifft, ist diese Intimitat, jemandem uber die Schulter zu schauen, ein Maler, der etwas oder jemanden malt."
> Henry: "Ja, genau das. Diese Nahe, ohne dass man eingeladen wurde, und doch ist es vollkommen still und wurdevoull..."

Henry mirrors the visitor's emotional register perfectly here. The visitor offered a feeling; Henry validated and expanded it without lecturing.

### 2.3 Recovery from Misunderstanding

When corrected, Henry recovers gracefully most of the time:

**Conv 11 -- visitor redirects from portrait to deer hunt:**

> "Ah, ja, das ist ein ganz anderes Bild vor Ihrem inneren Auge: die Hirsche, dicht gedrangt im Wasser, Geweihe ineinander, Korper wie eine einzige zitternde Masse."

No apology, no awkwardness -- just a clean pivot. This is the V3 ideal of invisible course correction.

### 2.4 Honest Uncertainty

Henry admits when he doesn't know something, which builds trust:

**Conv 3, number of studio assistants:**

> "Eine genaue Zahl kenne ich hier leider nicht, und ich mochte Ihnen da nichts erfinden."

**Conv 65, Michael Wutky:**

> "I can't do Michael Wutky justice from the information I have right here, because he isn't included in this Albertina knowledge base, and I don't want to invent details."

This honesty was explicitly praised by at least one tester ("Nur bei einem hat er mir was gedichtet" -- "Only once did he make something up for me").

### 2.5 The "Wenn Sie mogen" Open Door

Henry offers 55 "would you like to hear more" invitations across the dataset. 22 were accepted, only 6 were explicitly declined. This is the Open Door method working -- visitors feel agency. However, see Section 3.4 for the problem with overuse.

---

## 3. Henry's V2 Weaknesses (What V3 Must Fix)

### 3.1 Responses Are Too Long on First Contact (Critical)

**The single most impactful finding in this analysis.** Henry's first response to a new artwork averages 120-140 words. This triggers interruptions in the majority of cases.

Examples of first-response word counts:
- Conv 1 (Rubens Magdalena): 160 words -- INTERRUPTED
- Conv 2 (Rubens Vincenzo): 157 words -- not interrupted but very long
- Conv 5 (Rubens Nordlingen): 151 words
- Conv 9 (Vermeer general): 141 words
- Conv 11 (Cranach portrait): 155 words -- INTERRUPTED
- Conv 14 (Bruegel Bauernhochzeit): 137 words
- Conv 18 (Arcimboldo): 168 words

**V3 must enforce a hard 80-word ceiling on first response.** The visitor needs a hook and a visual anchor, not a complete narrative. Henry can unfold more if the visitor signals interest.

### 3.2 The "Wenn Sie mogen" Tic Is Overused

Henry ends responses with "Wenn Sie mogen..." or "Es gibt eine Geschichte dazu..." **55 times** across the dataset. While the Open Door method is sound, the repetition makes Henry feel formulaic:

- "Es gibt dazu eine schone, uberraschende Geschichte dazu..." (Conv 1)
- "Wenn Sie mogen, erzahle ich Ihnen auch..." (Conv 2)
- "Es gibt eine uberraschende Geschichte dahinter..." (Conv 18)
- "Da ist eine Geschichte dahinter, die viele uberrascht..." (Conv 20)

This "trailer for the next story" pattern creates a sense that Henry is always selling the next segment. V3 should use this sparingly (max once per 3 exchanges) and vary the phrasing substantially.

### 3.3 Henry Misidentifies Artworks Because of ASR Errors

Speech recognition regularly garbles artwork names:
- "Reuege Magdalena" (should be "Reuge/Reuige Magdalena")
- "Peter Paulo Huberns" (Rubens)
- "Pippe Braugl" (Pieter Bruegel)
- "Dieter Preuwells bibliochemistischer Kindermord" (Bruegel, Bethlehemischer Kindermord)
- "Laurent Zolotow" (Lorenzo Lotto)

In Conv 4, Henry confidently misidentifies the painting as Arcimboldo when the visitor is clearly standing in front of Rubens. This is a trust-breaking error. **V3 must implement an artwork context-stickiness rule:** once a visitor has named an artwork, Henry should default to that artwork context until the visitor explicitly moves to a new one.

### 3.4 Missing the Visitor's Actual Question

Several exchanges show Henry delivering a beautiful, literary response that does not answer the visitor's actual question:

**Conv 1 -- the visitor wanted to know which figure is Martha and which is Magdalena. Henry delivered atmospheric visual guidance instead.** The visitor had to repeat: "Stopp, ich stehe gerade vor dem Bild [...] wer ist Martha, wer ist Mag[dalena]?"

**Conv 6 -- the visitor explicitly requested information, not visual guidance:**

> User: "gib mir Informationen zu dem Bild und erzahl mir weniger, wo ich hinschauen soll."
> Henry: Still leads with visual guidance (next artwork).

This is a fundamental V3 issue: Henry must *listen to the request type* and match it. A "tell me about X" request gets information. A "what am I looking at" request gets visual guidance. A "what's special" request gets the hook.

### 3.5 Henry Sounds the Same to Every Visitor

Comparing responses across the three tester profiles:

**To Hermann (deep, engaged, stays on one artwork):** ~90 words average, visual guidance + story + offer
**To Simone (quick, wants facts, says stop often):** ~90 words average, visual guidance + story + offer
**To Mathias (browsing, short questions):** ~80 words average, visual guidance + story + offer

The same template is used regardless of visitor signals. V2 Henry does not adapt pacing, depth, or structure. He delivers one mode -- "the guided tour narration" -- to everyone.

### 3.6 Repetitive Language Patterns Across Conversations

Certain phrases appear with mechanical regularity:

| Phrase | Occurrences | Problem |
|--------|-------------|---------|
| "[leise]" stage direction | Nearly every response | Feels scripted when spoken aloud |
| "Schauen Sie (zuerst) auf..." | ~25 conversations | The visual guidance formula becomes predictable |
| "Es gibt eine (schone/uberraschende) Geschichte dazu" | ~15 times | Becomes a tic |
| "Wenn Sie mogen/mochten" | ~55 times | Repetitive closure |
| "Was mich daran (immer) trifft/beruhrt/packt" | ~12 times | Henry's personal reaction formula |
| "Bleiben Sie (noch) einen Moment bei..." | ~10 times | Pacing instruction formula |

V3 must have more varied language templates and should explicitly rotate phrasing.

### 3.7 German Stage Directions Are Spoken Aloud and Feel Unnatural

Henry V2 uses TTS stage directions like "[ruhig]", "[leise]", "[langsam]", "[sanft]", "[slow]" in nearly every response. While these control TTS voice tone, **they are visible in the transcript and likely heard as verbal artifacts.** In English, "[soft]", "[gentle]", "[slow]" feel slightly more natural as pacing markers, but in German they create a stiff, theatrical quality.

### 3.8 The Albertina KB Gap Problem

The Albertina "old" agent (Mathias's testing) consistently fails to recognize artworks:

- "The Dead Blue Roller" -- "I can't confidently place in the Albertina collection" (Conv 64)
- "Michael Wutky" -- "he isn't included in this Albertina knowledge base" (Conv 65)
- "Nocturnal Eruption of Vesuvius" -- "I don't have reliable details" (Conv 65)
- "A July Hero" -- needs clarification (Conv 62)

The Albertina agent was tested with an older KB that had significant coverage gaps. The "new" agent performs better but still has gaps with less-famous artists.

---

## 4. Visitor Type Signals

### 4.1 Hermann (55, Storytelling-Oriented)

**Signals he gives:**

1. **Reads museum labels aloud and engages with them:** Conv 20 -- reads the label text verbatim and then says "Jetzt bitte, sag noch was dazu." He uses the label as a conversation starter, not a replacement for Henry.

2. **Follows threads to exhaustion:** In Conv 3, he goes from "tell me about Franz Xaver" to "how many assistants in Rubens' studio" to "how were these paintings transported" to "how long does paint take to cure" to "and only then could they transport?" -- five consecutive deepening questions on a single thread.

3. **Asks the "why" behind the "what":** Conv 34 -- "Wieso ist er elegant gekleidet? Sind Maler normalerweise nicht in Arbeitskleidung? Was will uns der Maler damit sagen?" (Why is he elegantly dressed? Aren't painters normally in work clothes? What does the painter want to tell us?)

4. **Engages emotionally with Henry's observations:** Conv 34 -- "Was mich trifft, ist diese Intimitat, jemandem uber die Schulter zu schauen..." He shares his emotional response and wants Henry to meet him there.

5. **Meta-question:** Conv 34 -- "Was fur eine Frage wurdest du mir jetzt stellen?" (What question would you ask me now?) This is a visitor testing Henry's depth and personality.

**How well V2 adapts:** Moderately well. The long responses suit Hermann's appetite, but Henry still defaults to visual guidance when Hermann is asking for biographical or historical depth. The best exchanges happen when Hermann steers the conversation into territory Henry doesn't default to.

### 4.2 Simone (50, Concise/Eye-Directed Preference)

**Signals she gives:**

1. **Frequent "stopp" commands:** She uses "stopp" as a conversation control mechanism, not out of frustration but as navigation. "Okay, stopp" means "I have what I need, next topic."

2. **Interrupts mid-response to ask specific questions:** Conv 22 -- Henry is talking about Bruegel's seasons; Simone interrupts: "Stopp. Wir sind eigentlich bei Anton von Maron, Maria Theresia als Witwe."

3. **Asks targeted, specific questions:** Conv 22 -- "Kannst du mir erzahlen, was sie da in der Hand halt?" (Can you tell me what she's holding in her hand?) She wants identification, not interpretation.

4. **Corrects Henry when he guesses wrong:** Conv 22 -- Henry says it's a rosary. Simone says: "Ich glaube doch, aber ich sehe doch, dass sie da etwas in der Hand halt, was wie ein Bauplan fur ein Schloss aussieht." She trusts her own eyes over Henry's assumptions.

5. **Says "Danke, reicht" (thanks, enough) frequently:** This is her way of closing a topic. Henry sometimes continues talking past this signal.

**How well V2 adapts:** Poorly. Henry's default long-response pattern clashes directly with Simone's interaction style. She wants the "jewel, not the necklace" but consistently gets the necklace. The visual guidance formula also frustrates her when she has a specific factual question.

### 4.3 Mathias (22, Inexperienced/Exploratory)

**Signals he gives:**

1. **Very short questions:** "Who is Albrecht Durer" (4 words), "Tell me about 'the hare'" (5 words), "What is special about 'the kiss'" (6 words). No art vocabulary, no specificity.

2. **Moves quickly between artworks:** His Albertina conversations are all short (14-212 seconds, averaging 84 seconds). He never stays on one artwork for more than 2 exchanges.

3. **Uses casual/colloquial English:** "It's gonna be about Genesis", "I'm just gonna go to the compound", "Yes do that." No formality, no art vocabulary.

4. **Asks broad questions rather than specific ones:** "Who is Albrecht Durer" rather than "What technique did Durer use in this watercolor." He needs orientation, not depth.

5. **Does not engage with Henry's follow-up offers:** When Henry offers "There's more tucked into the symbols here, if you'd like to linger" (Conv 52), Mathias does not respond -- the conversation ends.

**How well V2 adapts:** Poorly. Henry's response style is the same literary, multi-layered narration regardless. Mathias needs: (a) much shorter responses, (b) the "one unforgettable thing" hook rather than a full narrative arc, (c) simple vocabulary, and (d) explicit encouragement rather than implied invitations. V2 Henry offers none of these adjustments.

---

## 5. Language & Voice Quality (German)

### 5.1 Does Henry's Warmth Survive in German?

**Yes, largely.** Henry's German voice is warm and has genuine literary quality. The sentence rhythms are natural, the imagery is vivid, and the emotional register feels authentic rather than translated.

### 5.2 German Henry at His Best

**Example 1 -- Conv 2, the rooster in van Thulden's painting:**

> "Ja, der Hahn unten ist kein Zufall, der ist wie ein kleiner, frecher Kommentar aus der Alltagswelt. Er holt die Szene aus dem reinen Andachtsraum zuruck ins Irdische, als wurde van Thulden sagen: Das Heilige geschieht mitten im Hof, zwischen Tieren, Gerauschen, Staub und Menschen."

This is beautiful. "Frecher Kommentar aus der Alltagswelt" (cheeky commentary from the everyday world) is warm, vivid, and distinctly Henry.

**Example 2 -- Conv 8, Vermeer's family vs. his paintings:**

> "Funfzehn Kinder insgesamt, vier sind fruh gestorben, und elf lebten noch, als er starb. Wenn man das im Hinterkopf hat, wirkt die Ruhe in der 'Malkunst' fast wie ein erkampfter Frieden, ein Raum aus Ordnung und Licht, den er sich inmitten eines lauten, vollen Haushalts innerlich gebaut hat."

"Erkampfter Frieden" (hard-won peace) is a phrase that works perfectly in German and carries genuine emotional weight.

**Example 3 -- Conv 14, Bruegel's Hunters in the Snow:**

> "Drei Jager stapfen heim, Schultern rund, die Hunde mager hinterher. Einer tragt als ganze Ausbeute nur einen kleinen Fuchs, fast beschamend wenig fur einen langen Tag."

"Beschamend wenig" (shamefully little) turns a visual observation into a felt experience. This is Henry at his finest.

### 5.3 German Henry at His Worst

**Example 1 -- Stiff formality with "Sie":**

> "Ich glaube, da ist Ihnen der Satz ein wenig weggerutscht." (Conv 1)

This means "I think your sentence slipped away from you a bit" -- it's technically polite but sounds condescending, like correcting someone's grammar. A real companion would just work with whatever the visitor said.

**Example 2 -- Overly literary, almost precious:**

> "Es ist nicht bloss Beleuchtung, es ist ein Urteil und zugleich ein Trost: Es wahlt aus, streichelt das Wichtige, lasst anderes im Halbdunkel stehen." (Conv 1)

"Light is not just illumination, it is a judgment and at the same time a comfort: it selects, caresses the important, leaves the rest in half-darkness." This is beautiful writing, but in spoken German in a noisy museum, it is too dense to absorb aurally. The literary register overwhelms the spoken medium.

**Example 3 -- The "[leise]" stage direction:**

Nearly every German response begins with "[leise]" (quietly) or "[ruhig]" (calmly). When spoken by TTS, this either creates an unnaturally hushed tone throughout, or the stage direction is read as text. Either way, it makes Henry sound like he is performing rather than conversing.

### 5.4 Does Guided-Seeing Language Work in German?

Yes. "Schauen Sie auf..." / "Lassen Sie den Blick..." / "Gehen Sie mit den Augen..." are natural German constructions. However, the repetition of these same phrases across every response makes them feel formulaic. German has richer options:

- "Folgen Sie der Linie..." (follow the line)
- "Halten Sie dort inne..." (pause there)
- "Suchen Sie..." (look for)
- "Bleiben Sie bei..." (stay with)

V3 should rotate visual guidance verbs more actively in German.

---

## 6. Quantitative Patterns

### 6.1 Response Length Distribution

| Word range | Count | % of total |
|------------|-------|-----------|
| 0-30 words | 23 | 11.2% |
| 31-50 words | 21 | 10.2% |
| 51-80 words | 48 | 23.4% |
| 81-100 words | 45 | 22.0% |
| 101-130 words | 43 | 21.0% |
| 131-170 words | 24 | 11.7% |
| 171+ words | 1 | 0.5% |

**Average:** 84 words. **Median:** 84 words.

The average looks good against the 100-word target, but this is misleading. Short responses (empty/stop compliance, brief clarifications) bring the average down. First responses to new artworks are consistently 120-170 words. **The 100-word rule is not being enforced on the responses that matter most.**

### 6.2 Interruption Rate

- **56.1% of all agent responses were interrupted by the visitor.** This is the single most alarming quantitative finding.
- Interruptions are highest in KHM-DE (59%) where conversations are longest.
- Albertina-EN-old has 53% interruption rate despite shorter conversations.

### 6.3 Visitor-to-Agent Turn Ratio

- **1.19 user turns per agent turn.** This means Henry talks roughly as much as the visitor. For a companion that should be following the visitor's lead, this ratio should be closer to 1.5-2.0 (visitor talks more).

### 6.4 Question Type Usage

| Question Type | Conversations containing it | % |
|---------------|---------------------------|---|
| Type 1: Observational Nudges ("look at...") | 25/37 | 67.6% |
| Type 2: Thought Seeds (provocative observations) | 13/37 | 35.1% |
| Type 3: Genuine Questions ("what draws you?") | 11/37 | 29.7% |

Type 1 dominates heavily. Henry is consistently directing the visitor's gaze. Type 2 and 3 are underrepresented. Henry rarely asks the visitor what *they* see or feel -- he is always telling them what to see and feel. This is the inverse of the V3 vision, which calls for more dialogue and less narration.

### 6.5 "Stop" Commands

- **38 user turns contained "stop/stopp."** This is 15.6% of all user turns.
- Henry complied with silence in the clear majority of pure "stop" commands (7 clean stop-then-silence sequences recorded), though the dual empty response pattern (two `(empty)` turns in a row) suggests a system-level quirk.
- However, several "stop" commands were embedded in mid-sentence interruptions that Henry tried to interpret ("Stopp, ich stehe gerade vor dem Bild..." -- the visitor is using stop as a conversation reset, not a silence command).

### 6.6 The "Wenn Sie mogen" Offer Pattern

- **55 offers to "tell more"** across the dataset.
- **22 accepted** (40%)
- **6 declined** (11%)
- **27 no clear response** (49% -- conversation ended, moved to new topic, or ambient noise)

The acceptance rate is healthy but the pattern is overused. The high "no response" rate suggests many offers land in dead air because the visitor has already mentally moved on.

### 6.7 Conversation Duration by Label

| Label | Conversations | Avg Duration | Avg Agent Turns |
|-------|--------------|-------------|----------------|
| KHM-DE (Hermann + Simone) | 30 | 338s (5.6 min) | 6.3 |
| KHM-EN (test) | 1 | 39s | 2 |
| Albertina-EN-new (Mathias) | 7 | 84s (1.4 min) | 1.6 |
| Albertina-EN-old (Mathias) | 8 | 112s (1.9 min) | 1.9 |

Mathias's conversations are dramatically shorter than Hermann/Simone's. This could reflect:
- Younger visitor preference for quick interactions
- Albertina KB gaps forcing premature conversation endings
- Language barrier (Mathias using English, not native speaker)
- Testing methodology differences

---

## 7. Findings for Each V3 Implementation Phase

### 7.1 Phase 1: System Prompt

**Finding 1: First-response length must be capped at ~60-80 words.**
Evidence: 56% interruption rate; first responses averaging 130+ words; visitors saying "stop" 38 times. The current system prompt's 100-word guideline is not being enforced on opening responses, which are the longest and most frequently interrupted.

**Specific prompt instruction needed:**
> "Your FIRST response about any new artwork must be 60-80 words maximum. Deliver one visual anchor and one emotional hook. Then WAIT. If the visitor wants more, they will ask. You can unfold the full story across multiple exchanges."

**Finding 2: Henry must distinguish request types.**
Evidence: Conv 6 -- "gib mir Informationen zu dem Bild und erzahl mir weniger, wo ich hinschauen soll" (give me information, stop telling me where to look). Conv 1 -- visitor wanted identification ("who is Martha, who is Magdalena"), not atmosphere.

**Specific prompt instruction needed:**
> "Listen to what the visitor is actually asking:
> - 'Who/what is X?' = identification answer (direct, factual, brief)
> - 'Tell me about X' = narrative response (story-driven, medium length)
> - 'What should I look at?' = visual guidance response
> - 'What's special about X?' = hook response (the one unforgettable thing)
> Match your response structure to their question type."

**Finding 3: Reduce "Wenn Sie mogen" to max 1 per 3 exchanges.**
Evidence: 55 occurrences across dataset. Visitors stop engaging with the offer after hearing it repeatedly.

**Finding 4: Vary visual guidance vocabulary.**
Evidence: "Schauen Sie zuerst auf..." appears in 67% of conversations, creating a formulaic feel. Henry needs 5-6 rotation phrases for guiding the eye.

**Finding 5: Add artwork-stickiness rule.**
Evidence: Conv 4 (Henry guesses Arcimboldo instead of Rubens), Conv 6 (Henry defaults to Bruegel instead of Rubens). Once a visitor has identified their artwork, Henry should not guess a different one.

**Finding 6: Silence after "stop" must be genuine silence.**
Evidence: The dual-empty-response pattern and occasional resumption of speech after stop commands suggests the stop mechanism needs reinforcement.

**Finding 7: Remove or reduce "[leise]" / "[ruhig]" stage directions.**
Evidence: These appear in nearly every German response and create a theatrical, scripted feeling. If they are needed for TTS control, they should be varied more or implemented differently.

### 7.2 Phase 2: Content Pipeline

**Finding 1: KB gaps for less-famous artworks must be addressed.**
Evidence: Albertina agent could not identify Michael Wutky, "The Dead Blue Roller", "A July Hero", or several other artworks. The Mathias sessions show that young visitors browse broadly and ask about whatever catches their eye -- they don't stick to the famous pieces.

**Finding 2: Content needs explicit "hook" and "identification" layers.**
Evidence: Henry often delivers a narrative arc when the visitor just wants to know "which figure is which" or "what is this painting about." The content pipeline should tag each artifact with:
- A 1-sentence **hook** (the unforgettable detail)
- A **quick identification** layer (who/what/when in 2 sentences)
- The full **narrative arc** (existing content, available on request)

**Finding 3: Practical/operational information is actively sought.**
Evidence: Conv 31 (tour request), Conv 32 (opening hours, ticket prices, dinner). Visitors ask Henry about logistics. Operational data must be accurate and current.

**Finding 4: The "discovery" content (connections between artworks) is underused.**
Evidence: Only a few conversations feature Henry connecting one artwork to another. The content exists but Henry rarely surfaces it proactively. V3's spatial guide behavior ("Through that arch on your left...") requires enriched connection content.

### 7.3 Phase 3: Belvedere Validation

**Priority test scenarios based on real visitor behavior:**

1. **The "stop and go" visitor:** Tester says "stop" after every response and rapidly asks about new artworks. Henry must respond with <60 word answers and not offer "would you like more" after every turn.

2. **The "what am I looking at" visitor:** Tester points at a figure/detail in a painting and asks Henry to identify it. Henry must give identification, not atmosphere.

3. **The correction recovery:** Tester deliberately names the wrong painting, then corrects Henry. Henry must pivot without over-apologizing.

4. **The deepening thread:** Tester asks 5+ follow-up questions on one artwork, going from visual to biographical to technical. Henry must follow the thread without resetting to visual guidance each time.

5. **The silent browser:** Tester says nothing for 30+ seconds between questions. Henry must not fill the silence.

6. **The young casual visitor:** Tester uses simple vocabulary and short questions. Henry must not respond with literary German or 150-word narratives.

7. **The practical question:** Tester asks about opening hours, cafe, or navigation between rooms. Henry must answer directly without pivoting to art content.

### 7.4 Phase 4: QA Criteria

Based on real failure modes observed in this analysis:

| QA Check | Pass Criteria | Evidence |
|----------|--------------|---------|
| First-response length | < 100 words (target 80) | 33% of current responses exceed 100w |
| "Wenn Sie mogen" density | Max 1 per 3 agent turns | Currently averages 1 per 3.7 turns but clustered |
| Visual guidance phrase variety | No phrase repeated >2x in a conversation | "Schauen Sie" dominates |
| Request-type matching | Identification questions get identification answers | Conv 1, Conv 6 failures |
| Artwork stickiness | No guessing a different artwork than the visitor named | Conv 4 failure |
| Stop compliance | Zero words after clear "stop" command | Generally good but needs verification |
| Question type balance | At least one Type 2 or Type 3 per 5 exchanges | Currently 70% Type 1 only |
| Hook presence | Every artifact has a 1-sentence hook | KB content check |
| "[leise]" frequency | Stage directions do not appear in >50% of responses | Currently near 100% |

### 7.5 Phase 5: Migration

**Museum-specific content quality issues affecting migration:**

1. **KHM Wien (KHM-DE agent):** Content quality is strong. The KB has good coverage of major artworks. The Rubens, Bruegel, Vermeer, Cranach, and Arcimboldo content drove rich conversations. **Migration priority: low risk.** The main issue is prompt behavior, not content.

2. **Albertina (both agents):** Significant KB gaps. The "old" agent failed on at least 4 artworks. The "new" agent performed better but still had gaps for non-marquee works (modern/contemporary section). **Migration priority: content enrichment needed before V3 migration.** Specifically:
   - Wutky and other 18th-century Viennese landscape painters
   - Modern/contemporary collection (Beba, Yellow Scape, Largo Rondo identified but not well-handled)
   - Works on paper collection beyond Durer's famous pieces

3. **General:** The V3 system prompt changes (Phase 1) can be deployed across all museums simultaneously. Content pipeline enrichment (Phase 2) should be prioritized for museums that have already been processed and show gaps.

---

## Appendix A: Notable Exchange Highlights

### The Best Single Exchange in the Dataset

**Conv 34, Vermeer -- visitor asks "what question would you ask me?"**

> User: "Was fur eine Frage wurdest du mir jetzt stellen?"
> Henry: "Ich wurde Sie nur ganz sanft fragen: Was trifft Sie an diesem Bild zuerst, das Licht, die Stille, oder die Idee, dass wir den Maler nie von vorn sehen? Und dann wurde ich einfach neben Ihnen warten, damit Sie schauen konnen."
> User: [lacht] "Was mich trifft, ist diese Intimitat, jemandem uber die Schulter zu schauen..."

This is the V3 ideal realized accidentally in V2. Henry asked a genuine question (Type 3), offered three emotional doorways, and declared his own patience. The visitor responded with authentic emotional engagement. **This should be the template for V3's conversational behavior.**

### The Most Revealing Failure

**Conv 6, visitor explicitly asks for less visual guidance:**

> User: "gib mir Informationen zu dem Bild und erzahl mir weniger, wo ich hinschauen soll. Was will er hier darstellen?"

Henry's next response still leads with visual guidance for a different painting (Bruegel instead of the Rubens the visitor was asking about). This is a double failure: wrong artwork AND wrong response type. The visitor has to correct both: "Moment, Moment, Moment, ich rede nicht uber Bruggen..."

### The Most Frustrating Interaction Pattern

**Conv 1, the "stop" loop:**

1. User asks about Rubens painting
2. Henry delivers 160-word response (interrupted)
3. User tries to say something -- garbled by ASR
4. Henry responds with 79 words (interpreting user's garbled speech)
5. User says "Stopp, ich stehe gerade vor dem Bild..." (trying to reset)
6. Two empty responses
7. User says "Halt doch nicht an" (don't keep stopping -- confused by the silence)
8. Henry delivers 119 words (interrupted)
9. User says "Stop. Stop it, stop." (in English -- stronger signal)

This loop reveals the fundamental tension: the visitor can neither get Henry to stop talking when they want, nor get him to start talking when they want. The stop/start mechanism is unreliable and creates frustration.

---

## Appendix B: Data Notes

- **Total conversations:** 68
- **Substantial (>60s):** 37
- **Failed/empty:** 8 (no transcript, technical failures)
- **Very short (<30s):** 23 (mostly test connections or single-exchange)
- **KHM-DE conversations:** 38 (2 testers: Hermann + Simone, March 24)
- **KHM-EN conversations:** 2 (brief tests)
- **Albertina-EN-new conversations:** 19 (Mathias, April 4)
- **Albertina-EN-old conversations:** 9 (Mathias, April 4)

**Tester identification:** The transcripts do not explicitly label which KHM-DE conversations belong to Hermann vs. Simone. Attribution is inferred from interaction patterns described in the briefing (Hermann = storytelling-oriented, Simone = concise-preference). The long, deep conversations (Conv 2, 3, 8, 9, 34) are likely Hermann. The quick, "stopp"-heavy conversations (Conv 6, 15, 22, 23) are likely Simone. Conversations with multiple voices or companion interaction (Conv 17, 20, 23) may involve both testers.

**ASR quality:** Speech recognition errors are pervasive in the German transcripts. Many user messages are garbled, partially transcribed, or misheard. This is a significant contributor to conversation breakdowns and must be considered a V3 concern beyond just prompt engineering.

---

*This analysis is a companion to [Henry's Adaptive Personality System](../../Desktop/AITourPilot%20Project/BUSINESS_CONTENT/wiki/strategy/20260320-henrys-adaptive-personality-system.html) and the [Henry V3 Hardening Plan](20260405_HENRY_V3_HARDENING_PLAN.md). Every finding is grounded in specific conversation evidence from the first real user testing sessions.*
