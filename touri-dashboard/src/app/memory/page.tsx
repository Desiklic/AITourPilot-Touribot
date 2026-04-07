'use client';

import { useEffect, useState, useRef } from 'react';
import { Brain, Search, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import type { Memory } from '@/lib/types';

// ─── Type badge colors ────────────────────────────────────────────────────────

type MemoryType = 'fact' | 'insight' | 'event' | 'error';

const TYPE_COLORS: Record<string, string> = {
  fact:    'bg-blue-500/20 text-blue-300 border-blue-500/30',
  insight: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  event:   'bg-green-500/20 text-green-300 border-green-500/30',
  error:   'bg-red-500/20 text-red-300 border-red-500/30',
};

const TYPE_FILTERS: Array<{ value: string; label: string }> = [
  { value: '',        label: 'All' },
  { value: 'fact',    label: 'Fact' },
  { value: 'insight', label: 'Insight' },
  { value: 'event',   label: 'Event' },
  { value: 'error',   label: 'Error' },
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

// ─── Memory card ──────────────────────────────────────────────────────────────

function MemoryCard({ memory }: { memory: Memory }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = memory.content.length > 200;
  const displayText = !expanded && isLong
    ? memory.content.slice(0, 200) + '…'
    : memory.content;

  const typeBadgeClass = TYPE_COLORS[memory.type] ?? TYPE_COLORS.event;

  return (
    <div className="group rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 hover:border-[var(--primary)]/40 transition-colors">
      {/* Content */}
      <p className="text-sm leading-relaxed whitespace-pre-wrap">{displayText}</p>

      {/* Footer row */}
      <div className="flex items-center gap-3 mt-3 flex-wrap">
        <Badge
          variant="outline"
          className={`text-[10px] px-2 py-0 border ${typeBadgeClass}`}
        >
          {memory.type}
        </Badge>

        {/* Importance bar */}
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

        <span className="text-[10px] text-[var(--muted-foreground)] ml-auto">
          {relativeTime(memory.created_at)}
        </span>

        {/* Expand toggle */}
        {isLong && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-[10px] text-[var(--muted-foreground)] hover:text-[var(--primary)] transition-colors"
          >
            {expanded ? (
              <>
                <ChevronUp className="w-3 h-3" />
                less
              </>
            ) : (
              <>
                <ChevronDown className="w-3 h-3" />
                more
              </>
            )}
          </button>
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
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function fetchMemories(q: string, type: string) {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (type)  params.set('type', type);
      if (q)     params.set('search', q);
      const res = await fetch(`/api/memory?${params.toString()}`);
      if (!res.ok) return;
      const data = await res.json();
      setMemories(data.memories ?? []);
      setTotal(data.total ?? 0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchMemories('', '');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = (val: string) => {
    setSearch(val);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      fetchMemories(val, typeFilter);
    }, 300);
  };

  const handleTypeFilter = (val: string) => {
    setTypeFilter(val);
    fetchMemories(search, val);
  };

  // Stats derived from current full fetch (unfiltered if no search/type active)
  const byType = memories.reduce<Record<string, number>>((acc, m) => {
    acc[m.type] = (acc[m.type] ?? 0) + 1;
    return acc;
  }, {});

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
              TouriBot knowledge base — facts, insights, and events from every session
            </p>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 space-y-4">
        {/* Stats row */}
        {!search && !typeFilter && (
          <div className="flex flex-wrap gap-3">
            <StatBadge label="Total" value={total} />
            <StatBadge label="Facts"    value={byType.fact    ?? 0} />
            <StatBadge label="Insights" value={byType.insight ?? 0} />
            <StatBadge label="Events"   value={byType.event   ?? 0} />
            <StatBadge label="Errors"   value={byType.error   ?? 0} />
          </div>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted-foreground)]" />
          <Input
            className="pl-9"
            placeholder="Search memories…"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
          />
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
          {(search || typeFilter) && (
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
                  : 'No memories in the database yet.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((memory) => (
              <MemoryCard key={memory.id} memory={memory} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
