# 20260409-android-audio-wiring-handoff-for-carsten

*Source: Business Wiki / development/20260409-android-audio-wiring-handoff-for-carsten.html*

## TL;DR

**One file needs changes: `LightElevenLabsService.ts`.** Add ~50 lines of `Platform.OS` checks to route Android audio calls to AudioBridge (which you already built). The native Kotlin layer is complete. This is a TypeScript wiring task.

```
iOS:     LightElevenLabsService -> AudioStreamPlayer.ts -> AudioStreamPlayerModule.swift (2,162 lines)
Android: LightElevenLabsService -> AudioBridge/index.ts -> AudioBridgeModule.kt (637 lines)
```

**Deadline:** Android release targeted for next week. iOS Fastlane build running now with all latest changes.

---

## Current State

### What You Built (Dec 2025 / Feb 2026)

**AudioBridgeModule.kt** (637 lines) -- complete, production-ready:
- PCM 16-bit playback via AudioTrack with jitter queue
- Microphone recording with RMS level calculation
- Epoch-based stale chunk rejection
- Turn lifecycle tracking
- Tail gate scheduling with frame-accurate drain monitoring
- Audio focus management (API 26+)
- Bluetooth SCO routing

**AudioRoutingModule.kt** (295 lines) -- complete:
- Device enumeration (speaker, earpiece, Bluetooth, wired)
- `setCommunicationDevice()` for API 31+, deprecated fallbacks for older Android
- Dynamic route switching

### What's Not Wired

`LightElevenLabsService.ts` (the main conversation service) imports `audioStreamPlayer` (iOS-only) and has three `if (Platform.OS !== 'ios') return;` guards that **skip all audio on Android**. It never imports or calls AudioBridge.

### AudioBridge iOS is a Stub (That's Fine)

`AudioBridgeModule.swift` is 111 lines of TODO stubs. iOS uses `AudioStreamPlayerModule.swift` (2,162 lines, battle-tested). **Do not try to unify iOS under AudioBridge** -- keep AudioStreamPlayer for iOS, AudioBridge for Android.

---

## Method Mapping

Every iOS call has a direct Android equivalent. The APIs are nearly identical because you designed AudioBridge to mirror AudioStreamPlayer's capabilities.

| Operation | iOS (AudioStreamPlayer) | Android (AudioBridge) | Notes |
|-----------|------------------------|----------------------|-------|
| Init | `audioStreamPlayer.initialize(16000)` | `AudioBridge.initialize(16000)` | Direct swap |
| Play chunk | `playChunkWithMeta(b64, turnId, chunkId)` | `playPcmChunk(b64, turnId, chunkId)` | Different method name |
| Stop/flush | `audioStreamPlayer.stop()` | `AudioBridge.flush()` | Different name, same effect |
| Set epoch | JS-side only | `AudioBridge.setEpoch(n)` | Android also has native epoch filtering |
| Tail gate | `scheduleSilenceTail(turnId, 20)` | `scheduleTailGate(turnId, 480, 450)` | Android takes tail+settle separately |
| Tail event | `event.turn` | `event.turnId` | **Different key name in event payload** |
| Begin turn | `audioStreamPlayer.beginTurn(turnId)` | No-op | Android playback thread is always ready |
| End turn | `audioStreamPlayer.endTurn(turnId)` | No-op | Not needed on Android |
| Force unlock | `audioStreamPlayer.forceUnlockTurn()` | No-op | No turn locking on Android |
| Format safeguards | `setFormatSafeguardsEnabled(true)` | No-op | AudioTrack handles PCM directly |
| Hands-free session | `ensureHandsFreeSession()` | No-op | AudioBridge uses USAGE_VOICE_COMMUNICATION |
| Mic start | `AudioRecord.start()` | `AudioBridge.startRecording()` | Different API entirely |
| Mic data | `AudioRecord.on('data', cb)` | `AudioBridge.addMicFrameListener(cb)` | Event has { base64, rms, timestamp } |
| Mic stop | `AudioRecord.stop()` | `AudioBridge.stopRecording()` | Direct swap |
| Route | `setRoutePreference(code)` (0/1/2) | `AudioBridge.setRoute(name)` | String vs numeric |
| Cleanup | `audioStreamPlayer.cleanup()` | `AudioBridge.cleanup()` | Direct swap |

---

## Lines to Change in LightElevenLabsService.ts

### Line 23: Add AudioBridge import

```typescript
import audioStreamPlayer from './AudioStreamPlayer';
import AudioBridge from '../modules/audio-bridge';  // ADD THIS
```

### Lines 187-202: beginTurn() -- guard iOS-specific calls

```typescript
async beginTurn() {
  this.currentTurnId++;
  if (Platform.OS === 'ios') {
    await audioStreamPlayer.prepareAudioGraphForTurn();
    await audioStreamPlayer.setFormatSafeguardsEnabled(true);
    await audioStreamPlayer.beginTurn(this.currentTurnId);
  }
  // Android: no-op -- playback thread is always ready
}
```

### Line 283: processQueue() -- play chunk

```typescript
if (Platform.OS === 'android') {
  await AudioBridge.playPcmChunk(chunk.base64, this.currentTurnId, chunk.chunkId);
} else {
  await audioStreamPlayer.playChunkWithMeta(chunk.base64, this.currentTurnId, chunk.chunkId);
}
```

> **Note:** Lines 294-319 (playback level extraction for orb visualization) are pure TypeScript -- base64 decode, RMS calc, levelBus enqueue. **No changes needed.** They work identically on both platforms.

### Lines 204-213: endTurn() -- tail gate

```typescript
async endTurn() {
  if (Platform.OS === 'android') {
    await AudioBridge.scheduleTailGate(this.currentTurnId, 480, 450);
  } else {
    await audioStreamPlayer.scheduleSilenceTail(this.currentTurnId, 20);
    await audioStreamPlayer.endTurn(this.currentTurnId);
  }
}
```

### Lines 149-154: setupNativeEventListeners() -- tail gate drained event

```typescript
if (Platform.OS === 'android') {
  this.tailGateListener = AudioBridge.addTailGateDrainedListener((event) => {
    if (event.turnId === this.currentTurnId) {
      console.log('[LELS] Android tailGateDrained turn=' + this.currentTurnId);
      this.onTailGateDrained();
    }
  });
} else {
  this.tailGateListener = audioStreamPlayer.addTailGateDrainedListener((event) => {
    if (event.turn === this.currentTurnId) {
      this.onTailGateDrained();
    }
  });
}
```

**Watch out:** iOS event uses `event.turn`, Android uses `event.turnId`.

### Lines 866-881: initRecorder() -- mic setup

```typescript
if (Platform.OS === 'android') {
  this.micFrameListener = AudioBridge.addMicFrameListener((event) => {
    this.handleMicData(event.base64);
  });
} else {
  AudioRecord.init({ sampleRate: 16000, channels: 1, bitsPerSample: 16, ... });
  AudioRecord.on('data', (data: string) => this.handleMicData(data));
}
```

### Lines 884-892: startRecording()

```typescript
if (Platform.OS === 'android') {
  await AudioBridge.startRecording();
} else {
  AudioRecord.start();
  await audioStreamPlayer.ensureHandsFreeSession();
}
```

### Lines 898-901: stopRecording()

```typescript
if (Platform.OS === 'android') {
  await AudioBridge.stopRecording();
} else {
  AudioRecord.stop();
}
```

### Lines 367, 506, 547: stop playback

```typescript
if (Platform.OS === 'android') {
  await AudioBridge.flush();
} else {
  await audioStreamPlayer.stop();
}
```

### Lines 371, 507, 544: forceUnlockTurn -- iOS only

```typescript
if (Platform.OS === 'ios') {
  await audioStreamPlayer.forceUnlockTurn();
}
```

### Lines 534-573: changeAudioRoute()

```typescript
if (Platform.OS === 'android') {
  await AudioBridge.setRoute(routeLower);  // 'speaker', 'earpiece', 'bluetooth'
} else {
  await audioStreamPlayer.setRoutePreference(routeCode);  // 0, 1, 2
}
```

### stopConversation(): cleanup

```typescript
if (Platform.OS === 'android') {
  this.tailGateListener?.remove();
  this.micFrameListener?.remove();
  await AudioBridge.cleanup();
} else {
  await audioStreamPlayer.cleanup();
}
```

---

## What Does NOT Need Changing

These are pure TypeScript and work identically on both platforms:

- **Barge-in detection** (`checkBargeIn()`, lines 334-353) -- 3-frame threshold + decay-adjusted RMS
- **Speaker echo gating** (`shouldSendMicFrame()`, lines 925-939) -- RMS threshold + 2s cooldown
- **Playback level extraction** (lines 294-319) -- base64 decode, RMS calc, levelBus enqueue for orb visualization
- **WebSocket management** -- connect, send, receive, reconnect with history injection
- **Conversation status machine** -- idle/connecting/connected/listening/speaking/processing/error
- **EOS transcript commit** (`ws.send("")` before close) -- just added Apr 8
- **AppState listener** (stop on background) -- just added Apr 8
- **All conversation history/memory logic**

---

## Feature Parity Verification

| Feature | iOS | Android | Parity |
|---------|-----|---------|--------|
| PCM playback quality | AVAudioConverter per chunk | ShortArray direct to AudioTrack | Equivalent |
| Orb level visualization | TypeScript RMS extraction | Same TypeScript code | Identical |
| Barge-in (3-frame + decay) | TypeScript logic | Same TypeScript logic | Identical |
| Speaker echo gate (2s cooldown) | TypeScript logic | Same TypeScript logic | Identical |
| Tail gate (HFP flush) | 480ms silence + native drain event | Silence + playback head monitor + drain event | Equivalent |
| Audio routing | AVAudioSession override | AudioManager mode + SCO | Equivalent |
| Mic recording | react-native-audio-record | AudioBridge native recording | Equivalent |
| RMS from mic | Computed in TypeScript | Computed natively in Kotlin (sent in event) | Equivalent |
| Epoch invalidation | TypeScript-side | Native queue filtering + TypeScript | Enhanced on Android |
| Reconnect with context | WebSocket + history injection | Same | Identical |

---

## Build & Test Commands

```bash
# Android dev APK for testing on device
npx eas build -p android --profile preview-apk

# After testing -- production bundle for Play Store
npx eas build -p android --profile production
npx eas submit -p android --latest
```

---

## Testing Checklist

After wiring, test on a real Android device:

- [ ] **Henry speaks** -- playback through speaker, earpiece, and Bluetooth
- [ ] **Henry hears you** -- mic frames reach WebSocket, agent responds
- [ ] **Orb pulses** -- visualization reacts to playback and mic levels
- [ ] **Barge-in works** -- speak over Henry, he stops and listens
- [ ] **Route switching** -- speaker to earpiece to Bluetooth, audio continues
- [ ] **Background stop** -- press home button, conversation stops cleanly (AppState listener)
- [ ] **Reconnect** -- toggle airplane mode, conversation resumes with history
- [ ] **Logout cleanup** -- log out mid-conversation, no dangling WebSocket
- [ ] **iOS regression** -- verify all 15 proven patterns still work unchanged

---

## Key File Paths

| File | What | Lines |
|------|------|-------|
| `services/LightElevenLabsService.ts` | **THE FILE TO CHANGE** -- add Platform checks | ~1,005 |
| `modules/audio-bridge/index.ts` | Cross-platform TS bridge (ready) | 226 |
| `modules/audio-bridge/android/.../AudioBridgeModule.kt` | Your Kotlin implementation (ready) | 637 |
| `modules/audio-bridge/ios/AudioBridgeModule.swift` | iOS stub (ignore -- iOS uses AudioStreamPlayer) | 111 |
| `modules/audio-routing/android/.../AudioRoutingModule.kt` | Your Kotlin routing (ready) | 295 |
| `services/AudioStreamPlayer.ts` | iOS-only bridge (do not modify) | 492 |
| `modules/audio-stream-player/ios/AudioStreamPlayerModule.swift` | iOS native (do not modify) | 2,162 |

---

## Also Needed for Play Store Release

| Item | Status | Action |
|------|--------|--------|
| **Production keystore** | Unknown -- check EAS credentials | `eas credentials` to verify or generate |
| **EAS submit config** | Missing from eas.json | Add `submit.production.android` block, or upload AAB manually via Play Console |
| **Version code** | Auto-incremented by EAS | Verify `autoIncrement: true` in eas.json production profile |

---

*This handoff was prepared April 9, 2026. The native Kotlin layer is production-ready. The task is ~50 lines of TypeScript Platform.OS checks in one file. All the hard audio engineering is already done.*
