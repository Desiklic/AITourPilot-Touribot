'use client';

import { useState } from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { StageBadge } from '@/components/pipeline/stage-badge';
import type { MuseumContactGroup } from '@/lib/types';
import type { PipelineStage } from '@/lib/types';

interface MuseumContactTableProps {
  museums: MuseumContactGroup[];
  onSelect: (museumId: number) => void;
}

type SortKey = 'museum' | 'stage' | 'contacts' | 'city' | 'source' | 'interactions' | 'last_activity';
type SortDir = 'asc' | 'desc';

function formatDateShort(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr.slice(0, 10);
  }
}

function sortMuseums(museums: MuseumContactGroup[], key: SortKey, dir: SortDir): MuseumContactGroup[] {
  return [...museums].sort((a, b) => {
    let valA: string | number | null = null;
    let valB: string | number | null = null;

    switch (key) {
      case 'museum':
        valA = a.museum_name.toLowerCase();
        valB = b.museum_name.toLowerCase();
        break;
      case 'stage':
        valA = a.museum_stage;
        valB = b.museum_stage;
        break;
      case 'contacts':
        valA = a.contacts.length;
        valB = b.contacts.length;
        break;
      case 'city':
        valA = (a.museum_city ?? '').toLowerCase();
        valB = (b.museum_city ?? '').toLowerCase();
        break;
      case 'source':
        valA = (a.museum_source ?? '').toLowerCase();
        valB = (b.museum_source ?? '').toLowerCase();
        break;
      case 'interactions':
        valA = a.interaction_count;
        valB = b.interaction_count;
        break;
      case 'last_activity':
        valA = a.last_interaction ?? '';
        valB = b.last_interaction ?? '';
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
      className="flex items-center gap-1 hover:text-foreground transition-colors whitespace-nowrap"
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

function truncateContacts(contacts: MuseumContactGroup['contacts'], maxLen = 60): string {
  const names = contacts.map((c) => c.full_name);
  if (names.length === 0) return '—';
  const joined = names.join(', ');
  if (joined.length <= maxLen) return joined;
  return joined.slice(0, maxLen - 1) + '…';
}

export function MuseumContactTable({ museums, onSelect }: MuseumContactTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('last_activity');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

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
              <SortButton col="museum" current={sortKey} dir={sortDir} label="Museum" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="stage" current={sortKey} dir={sortDir} label="Stage" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="contacts" current={sortKey} dir={sortDir} label="Contacts" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="city" current={sortKey} dir={sortDir} label="City" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="source" current={sortKey} dir={sortDir} label="Source" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="interactions" current={sortKey} dir={sortDir} label="Interactions" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="last_activity" current={sortKey} dir={sortDir} label="Last Activity" onSort={handleSort} />
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((museum) => (
            <tr
              key={museum.museum_id}
              onClick={() => onSelect(museum.museum_id)}
              className={cn(
                'border-b last:border-0 cursor-pointer transition-colors',
                'hover:bg-muted/40'
              )}
            >
              <td className="px-4 py-3 font-medium max-w-[200px]">
                <span className="truncate block">{museum.museum_name}</span>
              </td>
              <td className="px-4 py-3">
                <StageBadge stage={museum.museum_stage as PipelineStage} size="sm" />
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground max-w-[200px]">
                <span className="truncate block" title={museum.contacts.map((c) => c.full_name).join(', ')}>
                  {truncateContacts(museum.contacts)}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {museum.museum_city ?? <span className="opacity-40">—</span>}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {museum.museum_source ?? <span className="opacity-40">—</span>}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground text-center">
                {museum.interaction_count}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {formatDateShort(museum.last_interaction)}
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
