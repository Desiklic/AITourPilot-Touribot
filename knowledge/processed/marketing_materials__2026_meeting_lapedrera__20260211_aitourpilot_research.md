# 20260211_AITOURPILOT_RESEARCH

*Source: Marketing Materials / 2026 meeting_lapedrera/20260211_AITOURPILOT_RESEARCH.md*

# AITourPilot - Comprehensive Research Document

**Date:** 2026-02-11
**Project Path:** `~/Documents/ClaudeProjects/AITourPilot4`
**Branch:** `development`

---

## Executive Summary

AITourPilot is an AI-powered conversational audio guide that transforms museum visits into personalized, voice-driven experiences. Built as a React Native mobile app with ElevenLabs voice AI, it enables visitors to have real-time spoken conversations with an AI tour guide — asking questions, following their curiosity, and receiving adaptive storytelling — all without looking at a screen. The product serves both museum visitors (B2C) and museum institutions (B2B) looking to deepen visitor engagement.

---

## Business Goals

### Vision

To transform the way people experience art and culture — from passive observation to personal connection — by making every museum visit a meaningful, accessible, and engaging conversation.

### Mission

AITourPilot creates conversational, AI-powered audio guides that enable visitors to explore exhibitions through natural dialogue — sparking curiosity, deepening emotional engagement, and helping museums connect with broader, more diverse audiences without altering their exhibitions.

### Target Market

- **B2C:** Museum visitors and art enthusiasts who want deeper, more personal experiences with art. Early access signups via `engage.aitourpilot.com/visitors`.
- **B2B:** Museum decision-makers (directors, curators, marketing leads) seeking modern engagement tools. Demo requests via `engage.aitourpilot.com/museums`.
- **B2B2C model:** AITourPilot partners with museums to deliver the experience to their visitors.

### Business Model

Partnership-driven: museums integrate AITourPilot as their interactive guide offering, replacing or supplementing traditional audio guides. Revenue likely through institutional licensing/partnerships.

### Marketing Strategy

- **Brand tone:** Emotional + intellectual, not hard-sell
- **Key hashtag:** #FeelThePaint (play on "Feel the Pain")
- **Tagline:** "AITourPilot - The Future of Museum Experiences"
- **Launch approach:** Cinematic trailer (1:40 min) with teaser series across LinkedIn, TikTok, Instagram, YouTube Shorts
- **Paid campaigns:** LinkedIn Brand Awareness at ~€100/campaign targeting museum professionals in US/Europe/DACH

---

## Product Overview

### What It Does

Users open the app, select a museum from the available list, choose a language (English, Spanish, or German), and begin a voice conversation with an AI tour guide. The guide adapts to the visitor's interests, answers questions about artworks, shares hidden narratives and historical context, and personalizes the storytelling in real time.

### Key Features

- **Voice-first interaction:** Natural spoken conversation, no typing or screen-tapping required
- **Screen-free experience:** Visitors keep their eyes on the art, ears engaged with the guide
- **Multi-language support:** English, Spanish, and German for each museum
- **Per-museum AI agents:** Each museum has dedicated AI agents trained on its collection (via ElevenLabs)
- **Audio output flexibility:** Earpiece (default in museums for privacy), speaker, or Bluetooth
- **Barge-in / interruption support:** Users can interrupt the AI mid-speech naturally
- **Firebase authentication:** User accounts via Google Sign-In
- **Analytics:** Firebase Analytics integration for visitor behavior insights

### Currently Supported Museums (5 active)

| Museum | Location |
|--------|----------|
| Bletchley Park | Bletchley, England |
| La Pedrera - Casa Milà | Barcelona, Spain |
| Museum of Art and History (MAH) | Geneva, Switzerland |
| SS Great Britain | Bristol, England |
| Albertina | Vienna, Austria |

Additional museums are in the "coming soon" pipeline: Guggenheim Bilbao, Louvre, Rijksmuseum, Museumsquartier.

---

## Technical Architecture

### Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | React Native 0.79.5 (bare workflow) |
| **Language** | TypeScript (strict mode) |
| **Package Manager** | Yarn 4.10.2 |
| **Voice AI** | ElevenLabs Conversational AI (WebSocket + PCM streaming) |
| **Authentication** | Firebase Auth + Google Sign-In |
| **Analytics** | Firebase Analytics |
| **Navigation** | React Navigation (native stack + bottom tabs) |
| **State Management** | React Context API (AppContext + AuthContext) |
| **Audio** | Custom native modules + expo-av fallback |
| **UI** | React Native Reanimated, Shopify Skia, Lucide icons |
| **iOS Build** | Xcode + Fastlane → TestFlight |
| **Android Build** | EAS Build (not actively maintained) |

### Platform-Specific Audio Pipeline

```
Web:    ConvAI.tsx → @elevenlabs/react SDK → browser audio APIs
Mobile: NativeElevenLabsService.ts → WebSocket + 16kHz PCM streaming → native audio modules
```

The mobile audio pipeline is the core of the app and involves:
1. WebSocket connection to ElevenLabs via signed URL authentication
2. 16kHz mono PCM audio capture from microphone
3. Real-time streaming of user speech to ElevenLabs
4. Reception and sequential queuing of AI response audio chunks
5. Native playback through AVAudioEngine (iOS) with Bluetooth HFP support

### Custom Native Modules (`modules/`)

| Module | Purpose |
|--------|---------|
| `audio-routing` | Platform-specific audio output routing (earpiece/speaker/Bluetooth) |
| `audio-session-controller` | iOS AVAudioSession management |
| `audio-stream-player` | Native PCM audio playback with sequential queuing |
| `audio-bridge` | Audio bridging between JS and native layers |
| `reachability-monitor` | Network connectivity monitoring |

### Key Services (`services/`)

| Service | Purpose | Complexity |
|---------|---------|------------|
| `NativeElevenLabsService.ts` | Core mobile voice service: WebSocket, PCM streaming, turn-taking, barge-in | 3,200+ lines |
| `AudioRoutingService.ts` | Audio output route management (earpiece/speaker/BT) | Medium |
| `AudioStreamPlayer.ts` | Sequential audio chunk queuing to prevent overlap | Medium |
| `ElevenLabsConversationalService.ts` | Higher-level conversation orchestration | Medium |
| `OfficialElevenLabsService.ts` | Official ElevenLabs SDK integration path | Medium |
| `authService.ts` | Firebase authentication service | Small |
| `analyticsService.ts` | Firebase Analytics event tracking | Small |

### Key Components (`components/`)

| Component | Purpose |
|-----------|---------|
| `MuseumView.tsx` | Main museum experience screen with voice conversation |
| `HomeView.tsx` | Home/landing screen with museum selection |
| `MuseumContainerView.tsx` | Museum list/grid container |
| `ConvAI.tsx` | Web-based conversational AI component |
| `OfficialConvAI.tsx` | Official ElevenLabs SDK conversation component |
| `AudioOutputMenu.tsx` | Audio route selection UI (earpiece/speaker/BT) |
| `AudioOutputSelector.tsx` | Audio output selection control |
| `OrbView.tsx` | Visual voice activity indicator |
| `NebulaVoiceOverlay.tsx` | Visual overlay during voice interaction |
| `ChatView.tsx` | Text-based chat fallback view |
| `SideMenu.tsx` / `SideMenuView.tsx` | Navigation side menu |
| `NetworkIssueBubble.tsx` | Network connectivity warning UI |
| `SettingsMenu.tsx` | App settings interface |

### State Management

- **AppContext.tsx:** Global state for conversation, museum selection, language, recording state, audio source, and AI service configuration
- **AuthContext.tsx:** Firebase authentication state, Google Sign-In integration
- No Redux or Zustand — pure React Context API

---

## Current State

### Development Stage

The project is in **active development / pre-launch** stage:

- **iOS:** Primary platform, actively maintained. Bare workflow builds via Xcode + Fastlane to TestFlight.
- **Android:** EAS build setup exists but has not been actively maintained for months.
- **Web:** Basic support exists via ConvAI.tsx but mobile is the primary target.
- **5 museums live:** Bletchley Park, La Pedrera, MAH Geneva, SS Great Britain, Albertina — each with trilingual agent support.
- **Marketing launch:** Teaser campaign underway (Feb-Mar 2026), full trailer planned for mid-March.
- **Early access:** Visitor signup and museum demo request pages are live.

### Recent Development Activity

Based on recent git history:
- WebSocket connection timeout handling
- Network event deduplication
- Route change debounce logic
- Native Android integration fixes (Bluetooth support)
- Native iOS audio routing documentation
- Merge conflict resolution from parallel feature work

### Technical Maturity

The codebase shows significant depth in audio engineering:
- Extensive native module development for iOS audio (AVAudioEngine, AVAudioSession, Bluetooth HFP)
- Carefully calibrated speech detection thresholds (documented as "DO NOT MODIFY")
- Complex barge-in/interruption handling with buffer flushing
- Bluetooth HFP drain gate for timing audio completion
- The `NativeElevenLabsService.ts` at 3,200+ lines represents months of iterative audio engineering

### Known Constraints

- Metro bundler breaks native audio playback (must use Xcode Release builds for audio testing)
- Android requires 500ms delay after AudioRecord initialization
- expo-av must be isolated from native audio session on iOS (guarded via `audioSessionGuards.ts`)
- Bluetooth HFP requires tail padding and drain gates for proper audio completion

---

## Market Position

### Core Differentiators

1. **Voice-first, screen-free:** Unlike apps that require screen interaction (QR scanning, menu tapping, map browsing), AITourPilot is entirely audio-driven. Visitors keep their eyes on the art.

2. **Conversational, not scripted:** Traditional audio guides play pre-recorded tracks. AITourPilot enables real-time dialogue — visitors ask questions and the AI adapts its storytelling to their curiosity.

3. **Emotional connection:** The brand positioning emphasizes feeling art, not just observing it. The tagline "Feel the Paint" captures the aspiration to create emotional resonance, not just information delivery.

4. **Personalization at scale:** The AI learns visitor preferences in real-time, making each tour unique. No two experiences are the same.

5. **Museum-friendly deployment:** No changes to exhibitions required. Works alongside existing infrastructure. Provides museums with engagement analytics (dwell time, sentiment, exhibit performance).

6. **Multi-language:** Trilingual support (EN/ES/DE) from day one, addressing the international nature of museum tourism.

### What AITourPilot is NOT

- Not AR/VR — no headsets, no visual overlays
- Not a map/navigation app
- Not a replacement for human guides — it's a complement
- Not a one-way narrator — it's a two-way conversation

### Competitive Landscape

Traditional audio guides (Acoustiguide, Antenna Audio) offer pre-recorded linear content. Newer entrants use AI for text-based Q&A or AR overlays. AITourPilot's differentiation is the voice-first conversational approach with no screen dependency — positioned as the next evolution beyond both traditional and app-based guides.

---

## Key Files Reference

| File | Role |
|------|------|
| `CLAUDE.md` | Comprehensive development guide (289 lines) |
| `package.json` | Dependencies and scripts |
| `constants/Museum.ts` | Museum definitions, agent IDs, active museum list |
| `constants/AppConstants.ts` | App configuration, API keys, voice settings |
| `context/AppContext.tsx` | Global state: conversation, museum, language, recording |
| `context/AuthContext.tsx` | Firebase auth state |
| `services/NativeElevenLabsService.ts` | Core voice service (3,200+ lines) |
| `services/AudioRoutingService.ts` | Audio output routing |
| `services/AudioStreamPlayer.ts` | Sequential audio queuing |
| `components/MuseumView.tsx` | Main museum experience screen |
| `components/HomeView.tsx` | Home screen with museum selection |
| `components/ConvAI.tsx` | Web conversational AI component |
| `components/AudioOutputMenu.tsx` | Audio route selection UI |
| `utils/audioSessionGuards.ts` | expo-av isolation guards for native audio |
| `modules/audio-stream-player/` | Native PCM playback module |
| `modules/audio-routing/` | Native audio routing module |
| `modules/audio-session-controller/` | iOS audio session module |
| `modules/reachability-monitor/` | Network connectivity module |
| `ios/fastlane/` | iOS build automation |
| `.env` | ElevenLabs API key (not committed) |

---

## Asana Integration

| Property | Value |
|----------|-------|
| **Asana Project** | YC - Agent Execution |
| **Asana Project ID** | `1212655497011253` |
| **Workspace ID** | `1212647548393869` |

---

*Research compiled from: CLAUDE.md, package.json, source code analysis, business prompt document, marketing vision/mission document, and HenryBot project registry.*
