'use client';

import { useRef, useState, useCallback, useImperativeHandle, forwardRef, useEffect } from 'react';
import { Send, Loader2, Plus, X, FileText, Mic } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AttachmentPreview {
  file: File;
  previewUrl?: string;
  id: string;
}

export interface ChatInputProps {
  onSend: (message: string, files: File[]) => void;
  disabled?: boolean;
  sending?: boolean;
  initialValue?: string;
  onInitialValueConsumed?: () => void;
}

export interface ChatInputHandle {
  addFiles: (files: FileList | File[]) => void;
}

const MAX_FILES = 5;
const MAX_FILE_SIZE_MB = 10;
const ACCEPTED_TYPES = 'image/*,.md,.txt,.pdf,.docx,.doc,.csv,.json,.html,.log,.py,.ts,.tsx,.js,.jsx';

const LONG_PRESS_MS = 300;
const MIN_DURATION_MS = 300;
const MIN_SIZE_BYTES = 1000;
const CHAT_API = process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:8766';

export const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(function ChatInput(
  { onSend, disabled, sending, initialValue, onInitialValueConsumed },
  ref,
) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState('');
  const [attachments, setAttachments] = useState<AttachmentPreview[]>([]);

  // Pre-fill from initialValue (e.g. ?prompt= query param)
  useEffect(() => {
    if (initialValue) {
      setValue(initialValue);
      requestAnimationFrame(() => {
        const el = textareaRef.current;
        if (el) {
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 340) + 'px';
          el.focus();
          el.setSelectionRange(el.value.length, el.value.length);
        }
      });
      onInitialValueConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialValue]);

  const adjustHeight = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 340) + 'px';
  };

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const arr = Array.from(incoming).filter(
      (f) => f.size <= MAX_FILE_SIZE_MB * 1024 * 1024,
    );
    setAttachments((prev) => {
      const slots = MAX_FILES - prev.length;
      if (slots <= 0) return prev;
      const toAdd = arr.slice(0, slots).map((file) => ({
        file,
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        previewUrl: file.type.startsWith('image/')
          ? URL.createObjectURL(file)
          : undefined,
      }));
      return [...prev, ...toAdd];
    });
  }, []);

  useImperativeHandle(ref, () => ({ addFiles }), [addFiles]);

  // ── Voice recording ──────────────────────────────────────────────
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordStartRef = useRef(0);
  const recordMimeRef = useRef('');
  const longPressRef = useRef(false);
  const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cleanup stream on unmount
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  function pickMimeType(): string {
    const types = [
      'audio/webm;codecs=opus', 'audio/webm', 'audio/mp4',
      'audio/ogg;codecs=opus', 'audio/ogg',
    ];
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
    return '';
  }

  function guessExt(mime: string): string {
    if (mime.includes('ogg')) return 'ogg';
    if (mime.includes('mp4')) return 'mp4';
    if (mime.includes('wav')) return 'wav';
    return 'webm';
  }

  async function ensureStream(): Promise<boolean> {
    if (streamRef.current) {
      const tracks = streamRef.current.getAudioTracks();
      if (tracks.length > 0 && tracks[0].readyState === 'live') return true;
    }
    try {
      streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      return true;
    } catch {
      return false;
    }
  }

  async function startRecording() {
    if (isRecording || isTranscribing) return;
    const ok = await ensureStream();
    if (!ok || !streamRef.current) return;

    chunksRef.current = [];
    const mime = pickMimeType();
    recordMimeRef.current = mime;

    const recorder = new MediaRecorder(streamRef.current, mime ? { mimeType: mime } : undefined);
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => transcribeAudio();
    mediaRecorderRef.current = recorder;
    recordStartRef.current = Date.now();
    recorder.start();
    setIsRecording(true);
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }

  async function transcribeAudio() {
    const duration = Date.now() - recordStartRef.current;
    const blob = new Blob(chunksRef.current, { type: recordMimeRef.current });

    if (duration < MIN_DURATION_MS || blob.size < MIN_SIZE_BYTES) return;

    setIsTranscribing(true);
    try {
      const fd = new FormData();
      fd.append('audio', blob, `recording.${guessExt(recordMimeRef.current)}`);
      const res = await fetch(`${CHAT_API}/api/chat/transcribe`, { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.warn('Transcription error:', err);
        return;
      }
      const data = await res.json();
      if (data.text) {
        setValue((prev) => (prev ? `${prev} ${data.text}` : data.text));
        // Focus and resize textarea
        setTimeout(() => {
          textareaRef.current?.focus();
          adjustHeight();
        }, 0);
      }
    } catch (err) {
      console.warn('Transcription failed:', err);
    } finally {
      setIsTranscribing(false);
    }
  }

  // Dual mode: short click toggles, long press holds
  function handleMicDown() {
    if (isTranscribing) return;
    longPressRef.current = false;
    if (isRecording) {
      // Already recording from a previous short click — stop it
      stopRecording();
      return;
    }
    longPressTimerRef.current = setTimeout(() => {
      longPressRef.current = true;
      startRecording();
    }, LONG_PRESS_MS);
  }

  function handleMicUp() {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
    if (longPressRef.current && isRecording) {
      // Long press release — stop recording
      stopRecording();
      longPressRef.current = false;
    } else if (!longPressRef.current && !isRecording) {
      // Short click — toggle on
      startRecording();
    }
  }

  function clearLongPressTimer() {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }

  // ────────────────────────────────────────────────────────────────

  const removeAttachment = useCallback((id: string) => {
    setAttachments((prev) => {
      const found = prev.find((a) => a.id === id);
      if (found?.previewUrl) URL.revokeObjectURL(found.previewUrl);
      return prev.filter((a) => a.id !== id);
    });
  }, []);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed && attachments.length === 0) return;
    onSend(trimmed, attachments.map((a) => a.file));
    setValue('');
    attachments.forEach((a) => { if (a.previewUrl) URL.revokeObjectURL(a.previewUrl); });
    setAttachments([]);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  // Paste: capture pasted images
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    const imageFiles = Array.from(items)
      .filter((i) => i.kind === 'file' && i.type.startsWith('image/'))
      .map((i) => i.getAsFile())
      .filter(Boolean) as File[];
    if (imageFiles.length > 0) {
      e.preventDefault();
      addFiles(imageFiles);
    }
  };

  const isDisabled = !!disabled || !!sending;
  const canSend = !isDisabled && (value.trim().length > 0 || attachments.length > 0);

  return (
    <div className="border-t bg-background p-4 relative">
      {/* Attachment preview chips */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2.5">
          {attachments.map((att) => (
            <div key={att.id} className="relative group">
              {att.previewUrl ? (
                <div className="relative">
                  <img
                    src={att.previewUrl}
                    alt={att.file.name}
                    className="h-16 w-auto rounded-lg object-cover border border-border"
                  />
                  <button
                    type="button"
                    onClick={() => removeAttachment(att.id)}
                    className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-foreground/80 text-background flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Remove"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 bg-muted border border-border rounded-lg px-2.5 py-2 max-w-[160px]">
                  <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                  <span className="text-xs text-foreground/80 truncate flex-1 min-w-0">
                    {att.file.name}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeAttachment(att.id)}
                    className="shrink-0 text-muted-foreground/50 hover:text-foreground transition-colors"
                    title="Remove"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <form
        autoComplete="off"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2 items-end"
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) addFiles(e.target.files);
            e.target.value = ''; // reset so same file can be re-selected
          }}
        />

        {/* Safari AutoFill blocker */}
        <input type="text" name="prevent-autofill" style={{ display: 'none' }} tabIndex={-1} />

        {/* Attach button */}
        <Button
          type="button"
          size="icon"
          variant="ghost"
          disabled={isDisabled || attachments.length >= MAX_FILES}
          onClick={() => fileInputRef.current?.click()}
          className="shrink-0 rounded-xl h-[44px] w-[44px] text-muted-foreground hover:text-foreground hover:bg-muted"
          title={`Attach file (${attachments.length}/${MAX_FILES})`}
        >
          <Plus className="w-5 h-5" />
        </Button>

        {/* Message textarea */}
        <textarea
          ref={textareaRef}
          name="chat-message"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            adjustHeight();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          onPaste={handlePaste}
          placeholder={
            attachments.length > 0
              ? 'Add a caption... (or just press Send)'
              : 'Message Touri...'
          }
          disabled={isDisabled}
          autoComplete="off"
          data-form-type="other"
          data-lpignore="true"
          className="flex-1 resize-none bg-muted rounded-xl px-4 py-3 text-[15px] placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-[var(--primary)] min-h-[72px] max-h-[340px] transition-all"
          rows={3}
        />

        {/* Microphone button */}
        <button
          type="button"
          disabled={isDisabled || isTranscribing}
          onPointerDown={handleMicDown}
          onPointerUp={handleMicUp}
          onPointerLeave={() => {
            if (longPressRef.current && isRecording) {
              stopRecording();
              longPressRef.current = false;
            }
            clearLongPressTimer();
          }}
          onPointerCancel={() => {
            if (longPressRef.current && isRecording) {
              stopRecording();
              longPressRef.current = false;
            }
            clearLongPressTimer();
          }}
          aria-label={isRecording ? 'Recording — click to stop' : isTranscribing ? 'Transcribing...' : 'Hold to record, click to toggle'}
          title={isRecording ? 'Recording — click to stop' : isTranscribing ? 'Transcribing...' : 'Hold to record, click to toggle'}
          className={`shrink-0 rounded-xl h-[44px] w-[44px] flex items-center justify-center transition-all select-none touch-none ${
            isRecording
              ? 'bg-red-500 text-white animate-pulse'
              : isTranscribing
                ? 'bg-muted text-muted-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          }`}
        >
          {isTranscribing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        {/* Send button */}
        <Button
          type="submit"
          size="icon"
          disabled={!canSend}
          className="shrink-0 rounded-xl h-[44px] w-[44px]"
        >
          {sending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </form>

      {/* File count badge */}
      {attachments.length > 0 && (
        <p className="text-[11px] text-muted-foreground/70 mt-1.5 ml-1">
          {attachments.length}/{MAX_FILES} file{attachments.length !== 1 ? 's' : ''} attached
          {attachments.length >= MAX_FILES ? ' (limit reached)' : ''}
        </p>
      )}
    </div>
  );
});
