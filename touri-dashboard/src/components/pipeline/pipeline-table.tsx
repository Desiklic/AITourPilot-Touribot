'use client';

import { useState } from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StageBadge } from './stage-badge';
import { ScoreBadge } from './score-badge';
import type { MuseumListItem } from '@/lib/types';

interface PipelineTableProps {
  museums: MuseumListItem[];
  onSelect: (id: number) => void;
}

type SortKey = 'name' | 'location' | 'stage' | 'score' | 'contact' | 'last_activity' | 'source';
type SortDir = 'asc' | 'desc';

function getLocationText(m: MuseumListItem): string {
  if (m.city && m.country) return `${m.city}, ${m.country}`;
  if (m.country) return m.country;
  return m.source ?? '—';
}

function getDaysSinceText(lastActivity: string | null): string {
  if (!lastActivity) return '—';
  const diff = Date.now() - new Date(lastActivity).getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return 'Today';
  if (days === 1) return '1 day ago';
  return `${days}d ago`;
}

function sortMuseums(museums: MuseumListItem[], key: SortKey, dir: SortDir): MuseumListItem[] {
  return [...museums].sort((a, b) => {
    let valA: string | number | null = null;
    let valB: string | number | null = null;

    switch (key) {
      case 'name':
        valA = a.name.toLowerCase();
        valB = b.name.toLowerCase();
        break;
      case 'location':
        valA = getLocationText(a).toLowerCase();
        valB = getLocationText(b).toLowerCase();
        break;
      case 'stage':
        valA = a.stage;
        valB = b.stage;
        break;
      case 'score':
        valA = a.score ?? -1;
        valB = b.score ?? -1;
        break;
      case 'contact':
        valA = (a.primary_contact_name ?? '').toLowerCase();
        valB = (b.primary_contact_name ?? '').toLowerCase();
        break;
      case 'last_activity':
        valA = a.last_activity ?? '';
        valB = b.last_activity ?? '';
        break;
      case 'source':
        valA = (a.source ?? '').toLowerCase();
        valB = (b.source ?? '').toLowerCase();
        break;
    }

    if (valA === null) valA = '';
    if (valB === null) valB = '';

    if (valA < valB) return dir === 'asc' ? -1 : 1;
    if (valA > valB) return dir === 'asc' ? 1 : -1;
    return 0;
  });
}

interface SortButtonProps {
  col: SortKey;
  current: SortKey;
  dir: SortDir;
  label: string;
  onSort: (key: SortKey) => void;
}

function SortButton({ col, current, dir, label, onSort }: SortButtonProps) {
  const isActive = current === col;
  return (
    <button
      onClick={() => onSort(col)}
      className="flex items-center gap-1 hover:text-foreground transition-colors"
    >
      {label}
      {isActive ? (
        dir === 'asc' ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />
      ) : (
        <ArrowUpDown className="size-3 opacity-40" />
      )}
    </button>
  );
}

export function PipelineTable({ museums, onSelect }: PipelineTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('stage');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sorted = sortMuseums(museums, sortKey, sortDir);

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/40">
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="name" current={sortKey} dir={sortDir} label="Museum" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="location" current={sortKey} dir={sortDir} label="Location" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="stage" current={sortKey} dir={sortDir} label="Stage" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="score" current={sortKey} dir={sortDir} label="Score" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="contact" current={sortKey} dir={sortDir} label="Primary Contact" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="last_activity" current={sortKey} dir={sortDir} label="Last Activity" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="source" current={sortKey} dir={sortDir} label="Source" onSort={handleSort} />
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((museum) => (
            <tr
              key={museum.id}
              onClick={() => onSelect(museum.id)}
              className={cn(
                'border-b last:border-0 cursor-pointer transition-colors',
                'hover:bg-muted/40'
              )}
            >
              <td className="px-4 py-3 font-medium max-w-[200px]">
                <span className="line-clamp-1">{museum.name}</span>
              </td>
              <td className="px-4 py-3 text-muted-foreground text-xs">
                {getLocationText(museum)}
              </td>
              <td className="px-4 py-3">
                <StageBadge stage={museum.stage} size="md" />
              </td>
              <td className="px-4 py-3">
                <ScoreBadge score={museum.score} />
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {museum.primary_contact_name ?? <span className="opacity-40">—</span>}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {getDaysSinceText(museum.last_activity)}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {museum.source ?? <span className="opacity-40">—</span>}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground text-sm">
                No museums match the current filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
