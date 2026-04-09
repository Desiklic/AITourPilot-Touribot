# 20260406-artifact-content-prompt-v3

*Source: Business Wiki / prompts/content-pipeline-v3-henry/20260406-artifact-content-prompt-v3.html*

## Artifact Content Prompt V3

**Version:** V3 — 7-Layer Adaptive Content
**File:** `src/lib/prompts/content.ts` (`generateArtifactContentPrompt()`)

### What Changed from V2
| Layer | V2 | V3 |
|-------|----|----|  
| Hook | Implicit in opening | Explicit first layer — one sentence that makes anyone want to know more |
| Quick ID | Missing | New — who/what/when in 2 sentences for identification questions |
| Visual Journey | "Guided Seeing" section | Enhanced with type-specific instructions (2D, 3D, spatial) |
| Human Story | Present | Enriched with IpRegistry emotional narratives when available |
| Deep Thread | Blended into "What Makes This Special" | Standalone layer for expert visitors |
| Wonder Moment | "Hidden Detail" | Enhanced with IpRegistry discoveries when available |
| Connection | Missing | New — cross-references real artworks from same museum via artifact roster |

### New Parameters
- `discoveries?: string` — IpRegistry content for Wonder Moment context
- `connections?: string` — IpRegistry connections + artifact roster for Connection layer

Both are optional for backward compatibility.

See the full prompt in `src/lib/prompts/content.ts`.
