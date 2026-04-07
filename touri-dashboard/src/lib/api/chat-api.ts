const CHAT_API = process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:8765';

export interface ChatSession {
  session_id: string;
  title: string | null;
  preview: string | null;
  message_count: number;
  created_at: string;
  last_message_at: string;
}

export interface ChatMessage {
  id: number;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  streaming?: boolean; // frontend-only, not persisted
}

export async function getSessions(): Promise<ChatSession[]> {
  const res = await fetch(`${CHAT_API}/api/chat/sessions`);
  if (!res.ok) throw new Error('Failed to fetch sessions');
  const data = await res.json();
  return data.sessions;
}

export async function getMessages(sessionId: string, sinceId?: number): Promise<ChatMessage[]> {
  let url = `${CHAT_API}/api/chat/messages?session_id=${sessionId}`;
  if (sinceId) url += `&since_id=${sinceId}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch messages');
  const data = await res.json();
  return data.messages;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${CHAT_API}/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
}

export function streamChat(
  message: string,
  sessionId: string | null,
): { stream: ReadableStream<string>; abort: () => void } {
  const controller = new AbortController();
  const stream = new ReadableStream<string>({
    async start(ctrl) {
      try {
        const res = await fetch(`${CHAT_API}/api/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, session_id: sessionId }),
          signal: controller.signal,
        });
        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) {
          ctrl.close();
          return;
        }
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              ctrl.enqueue(line.slice(6));
            }
          }
        }
        ctrl.close();
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          ctrl.error(err);
        }
        ctrl.close();
      }
    },
  });
  return { stream, abort: () => controller.abort() };
}
