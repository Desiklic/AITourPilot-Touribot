'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Brain,
  Search,
  ChevronDown,
  ChevronUp,
  Loader2,
  Trash2,
  Pencil,
  Check,
  X,
  Building2,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import type { Memory, MuseumListItem } from '@/lib/types';

// ─── Constants ─────────────────────────────────────────────────────────────────

const FASTAPI_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// New types + legacy types — all handled gracefully
const TYPE_COLORS: Record<string, string> = {
  contact_intel:  'bg-violet-500/20 text-violet-300 border-violet-500/30',
  museum_intel:   'bg-blue-500/20 text-blue-300 border-blue-500/30',
  interaction:    'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  strategy:       'bg-amber-500/20 text-amber-300 border-amber-500/30',
  research:       'bg-teal-500/20 text-teal-300 border-teal-500/30',
  general:        'bg-zinc-500/20 text-zinc-300 border-zinc-500/30',
  // Legacy types
  fact:           'bg-blue-500/20 text-blue-300 border-blue-500/30',
  insight:        'bg-purple-500/20 text-purple-300 border-purple-500/30',
  event:          'bg-green-500/20 text-green-300 border-green-500/30',
  error:          'bg-red-500/20 text-red-300 border-red-500/30',
};

const SOURCE_COLORS: Record<string, string> = {
  extraction: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  manual:     'bg-orange-500/15 text-orange-400 border-orange-500/30',
  research:   'bg-teal-500/15 text-teal-400 border-teal-500/30',
  cli:        'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
};

const TYPE_FILTERS: Array<{ value: string; label: string }> = [
  { value: '',              label: 'All' },
  { value: 'contact_intel', label: 'Contact Intel' },
  { value: 'museum_intel',  label: 'Museum Intel' },
  { value: 'interaction',   label: 'Interaction' },
  { value: 'strategy',      label: 'Strategy' },
  { value: 'research',      label: 'Research' },
  { value: 'general',       label: 'General' },
  // Legacy
  { value: 'fact',          label: 'Fact' },
  { value: 'insight',       label: 'Insight' },
  { value: 'event',         label: 'Event' },
  { value: 'error',         label: 'Error' },
];

const MEMORY_TYPES = [
  'contact_intel', 'museum_intel', 'interaction', 'strategy',
  'research', 'general', 'fact', 'insight', 'event', 'error',
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

function importanceColor(importance: number): string {
  if (importance >= 8) return 'bg-amber-500';
  if (importance >= 5) return 'bg-blue-400';
  return 'bg-zinc-500';
}

function parseTags(tags: string | null): string[] {
  if (!tags) return [];
  try {
    const parsed = JSON.parse(tags);
    if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean);
  } catch {
    // not JSON — treat as comma-separated
    return tags.split(',').map((t) => t.trim()).filter(Boolean);
  }
  return [];
}

// ─── Delete / Edit API calls ──────────────────────────────────────────────────

async function apiDeleteMemory(id: number): Promise<boolean> {
  try {
    const res = await fetch(`${FASTAPI_BASE}/chat/memory/${id}`, { method: 'DELETE' });
    return res.ok;
  } catch {
    return false;
  }
}

async function apiUpdateMemory(
  id: number,
  updates: Partial<Pick<Memory, 'content' | 'type' | 'importance' | 'museum_id'>>,
): Promise<Memory | null> {
  try {
    const res = await fetch(`${FASTAPI_BASE}/chat/memory/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!res.ok) return null;
    return (await res.json()) as Memory;
  } catch {
    return null;
  }
}

// ─── Memory card ──────────────────────────────────────────────────────────────

interface MemoryCardProps {
  memory: Memory;
  museumName: string | null;
  onDeleted: (id: number) => void;
  onUpdated: (updated: Memory) => void;
}

function MemoryCard({ memory, museumName, onDeleted, onUpdated }: MemoryCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);

  // Edit state
  const [editContent, setEditContent] = useState(memory.content);
  const [editType, setEditType] = useState(memory.type);
  const [editImportance, setEditImportance] = useState(memory.importance);

  const isLong = memory.content.length > 200;
  const displayText = !expanded && isLong
    ? memory.content.slice(0, 200) + '…'
    : memory.content;

  const typeBadgeClass = TYPE_COLORS[memory.type] ?? 'bg-zinc-500/20 text-zinc-300 border-zinc-500/30';
  const sourceBadgeClass = SOURCE_COLORS[memory.source ?? ''] ?? 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30';

  const tags = parseTags(memory.tags);

  const handleDelete = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setDeleting(true);
    const ok = await apiDeleteMemory(memory.id);
    if (ok) {
      onDeleted(memory.id);
    } else {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    const updated = await apiUpdateMemory(memory.id, {
      content: editContent,
      type: editType,
      importance: editImportance,
    });
    setSaving(false);
    if (updated) {
      onUpdated(updated);
      setEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditContent(memory.content);
    setEditType(memory.type);
    setEditImportance(memory.importance);
    setEditing(false);
  };

  return (
    <div className="group rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 hover:border-[var(--primary)]/40 transition-colors">

      {/* Museum name (when linked) */}
      {museumName && (
        <div className="flex items-center gap-1.5 mb-2">
          <Building2 className="w-3 h-3 text-[var(--muted-foreground)]" />
          <span className="text-[10px] text-[var(--muted-foreground)] font-medium">{museumName}</span>
        </div>
      )}

      {/* Content — editable or read-only */}
      {editing ? (
        <textarea
          className="w-full text-sm leading-relaxed bg-[var(--background)] border border-[var(--border)] rounded p-2 resize-y min-h-[80px] focus:outline-none focus:border-[var(--primary)]/60"
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          autoFocus
        />
      ) : (
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{displayText}</p>
      )}

      {/* Footer row */}
      <div className="flex items-center gap-3 mt-3 flex-wrap">

        {/* Type badge — selectable when editing */}
        {editing ? (
          <select
            className="text-[10px] bg-[var(--background)] border border-[var(--border)] rounded px-2 py-1 text-[var(--foreground)]"
            value={editType}
            onChange={(e) => setEditType(e.target.value)}
          >
            {MEMORY_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        ) : (
          <Badge
            variant="outline"
            className={`text-[10px] px-2 py-0 border ${typeBadgeClass}`}
          >
            {memory.type}
          </Badge>
        )}

        {/* Source badge */}
        {memory.source && !editing && (
          <Badge
            variant="outline"
            className={`text-[10px] px-2 py-0 border ${sourceBadgeClass}`}
          >
            {memory.source}
          </Badge>
        )}

        {/* Importance bar — editable as number when editing */}
        {editing ? (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--muted-foreground)]">Importance:</span>
            <input
              type="number"
              min={1}
              max={10}
              className="w-14 text-[10px] bg-[var(--background)] border border-[var(--border)] rounded px-1 py-0.5 text-center"
              value={editImportance}
              onChange={(e) => setEditImportance(Math.min(10, Math.max(1, Number(e.target.value))))}
            />
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            <div className="flex gap-0.5">
              {Array.from({ length: 10 }, (_, i) => (
                <div
                  key={i}
                  className={`h-1.5 w-1.5 rounded-full ${
                    i < memory.importance
                      ? importanceColor(memory.importance)
                      : 'bg-[var(--border)]'
                  }`}
                />
              ))}
            </div>
            <span className="text-[10px] text-[var(--muted-foreground)]">
              {memory.importance}/10
            </span>
          </div>
        )}

        {/* Tags */}
        {tags.length > 0 && !editing && (
          <div className="flex items-center gap-1 flex-wrap">
            {tags.map((tag) => (
              <span
                key={tag}
                className="text-[9px] px-1.5 py-0.5 rounded-full bg-[var(--primary)]/10 text-[var(--primary)] border border-[var(--primary)]/20"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <span className="text-[10px] text-[var(--muted-foreground)] ml-auto">
          {relativeTime(memory.created_at)}
        </span>

        {/* Expand toggle (read mode only) */}
        {isLong && !editing && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] hover:text-[var(--primary)] transition-colors"
          >
            {expanded ? (
              <><ChevronUp className="w-3 h-3" />less</>
            ) : (
              <><ChevronDown className="w-3 h-3" />more</>
            )}
          </button>
        )}

        {/* Action buttons */}
        {editing ? (
          <>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1 text-[10px] text-emerald-400 hover:text-emerald-300 transition-colors disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
              Save
            </button>
            <button
              onClick={handleCancelEdit}
              className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
            >
              <X className="w-3 h-3" />
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] hover:text-[var(--primary)] transition-colors opacity-0 group-hover:opacity-100"
            >
              <Pencil className="w-3 h-3" />
              Edit
            </button>

            <button
              onClick={handleDelete}
              disabled={deleting}
              onBlur={() => setConfirmDelete(false)}
              className={`flex items-center gap-1 text-[10px] transition-colors opacity-0 group-hover:opacity-100 ${
                confirmDelete
                  ? 'text-red-400 hover:text-red-300'
                  : 'text-[var(--muted-foreground)] hover:text-red-400'
              } disabled:opacity-50`}
            >
              {deleting ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Trash2 className="w-3 h-3" />
              )}
              {confirmDelete ? 'Confirm?' : 'Delete'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Stat badge ───────────────────────────────────────────────────────────────

function StatBadge({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)]">
      <span className="text-xs text-[var(--muted-foreground)]">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [museumFilter, setMuseumFilter] = useState<number | ''>('');
  const [museums, setMuseums] = useState<MuseumListItem[]>([]);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Museum id → name lookup
  const museumMap = useRef<Map<number, string>>(new Map());
  useEffect(() => {
    fetch('/api/leads')
      .then((r) => r.json())
      .then((data: { museums?: MuseumListItem[] }) => {
        const list = data.museums ?? [];
        setMuseums(list);
        const m = new Map<number, string>();
        list.forEach((mu) => m.set(mu.id, mu.name));
        museumMap.current = m;
      })
      .catch(() => { /* silently ignore */ });
  }, []);

  const fetchMemories = useCallback(async (q: string, type: string, museumId: number | '') => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (type)     params.set('type', type);
      if (q)        params.set('search', q);
      if (museumId !== '') params.set('museum_id', String(museumId));
      const res = await fetch(`/api/memory?${params.toString()}`);
      if (!res.ok) return;
      const data = await res.json();
      setMemories(data.memories ?? []);
      setTotal(data.total ?? 0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMemories('', '', '');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = (val: string) => {
    setSearch(val);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      fetchMemories(val, typeFilter, museumFilter);
    }, 300);
  };

  const handleTypeFilter = (val: string) => {
    setTypeFilter(val);
    fetchMemories(search, val, museumFilter);
  };

  const handleMuseumFilter = (val: string) => {
    const id = val === '' ? '' : parseInt(val, 10);
    setMuseumFilter(id);
    fetchMemories(search, typeFilter, id);
  };

  const handleDeleted = (id: number) => {
    setMemories((prev) => prev.filter((m) => m.id !== id));
    setTotal((prev) => prev - 1);
  };

  const handleUpdated = (updated: Memory) => {
    setMemories((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
  };

  // Stats derived from current fetch
  const byType = memories.reduce<Record<string, number>>((acc, m) => {
    acc[m.type] = (acc[m.type] ?? 0) + 1;
    return acc;
  }, {});

  const isFiltered = !!(search || typeFilter || museumFilter !== '');

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      {/* Header */}
      <div className="border-b border-[var(--border)] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[var(--primary)]/20 flex items-center justify-center">
            <Brain className="w-5 h-5 text-[var(--primary)]" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Memory</h1>
            <p className="text-xs text-[var(--muted-foreground)]">
              TouriBot knowledge base — contact intel, museum intel, strategy, and interactions
            </p>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 space-y-4">
        {/* Stats row */}
        {!isFiltered && (
          <div className="flex flex-wrap gap-3">
            <StatBadge label="Total" value={total} />
            {Object.entries(byType)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 6)
              .map(([type, count]) => (
                <StatBadge key={type} label={type} value={count} />
              ))}
          </div>
        )}

        {/* Search + Museum filter row */}
        <div className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted-foreground)]" />
            <Input
              className="pl-9"
              placeholder="Search memories…"
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>

          {/* Museum filter dropdown */}
          <select
            value={museumFilter === '' ? '' : String(museumFilter)}
            onChange={(e) => handleMuseumFilter(e.target.value)}
            className="text-sm bg-[var(--card)] border border-[var(--border)] rounded-md px-3 py-2 text-[var(--foreground)] min-w-[160px] focus:outline-none focus:border-[var(--primary)]/60"
          >
            <option value="">All museums</option>
            {museums.map((mu) => (
              <option key={mu.id} value={String(mu.id)}>
                {mu.name}
              </option>
            ))}
          </select>
        </div>

        {/* Type filter chips */}
        <div className="flex items-center gap-2 flex-wrap">
          {TYPE_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => handleTypeFilter(f.value)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                typeFilter === f.value
                  ? 'bg-[var(--primary)]/20 text-[var(--primary)] border-[var(--primary)]/40'
                  : 'bg-transparent text-[var(--muted-foreground)] border-[var(--border)] hover:border-[var(--primary)]/40 hover:text-[var(--primary)]'
              }`}
            >
              {f.label}
              {f.value && byType[f.value] != null ? (
                <span className="ml-1.5 opacity-60">{byType[f.value]}</span>
              ) : null}
            </button>
          ))}
          {isFiltered && (
            <span className="text-xs text-[var(--muted-foreground)] ml-auto">
              {memories.length} result{memories.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Memory list */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-[var(--muted-foreground)]" />
          </div>
        ) : memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-[var(--muted-foreground)]">
            <Brain className="w-10 h-10 opacity-30" />
            <p className="text-sm">
              {search
                ? `No memories matching "${search}"`
                : typeFilter
                  ? `No ${typeFilter} memories found`
                  : museumFilter !== ''
                    ? 'No memories for this museum'
                    : 'No memories in the database yet.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                museumName={memory.museum_id != null ? (museumMap.current.get(memory.museum_id) ?? null) : null}
                onDeleted={handleDeleted}
                onUpdated={handleUpdated}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
