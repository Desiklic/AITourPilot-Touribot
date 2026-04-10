'use client';

import { useState } from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { StageBadge } from '@/components/pipeline/stage-badge';
import type { ContactListItem } from '@/lib/types';
import type { PipelineStage } from '@/lib/types';

interface ContactTableProps {
  contacts: ContactListItem[];
  onSelect: (id: number) => void;
}

type SortKey = 'name' | 'role' | 'museum' | 'stage' | 'email' | 'source' | 'interactions' | 'last_activity';
type SortDir = 'asc' | 'desc';

function formatDateShort(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr.slice(0, 10);
  }
}

function sortContacts(contacts: ContactListItem[], key: SortKey, dir: SortDir): ContactListItem[] {
  return [...contacts].sort((a, b) => {
    let valA: string | number | null = null;
    let valB: string | number | null = null;

    switch (key) {
      case 'name':
        valA = a.full_name.toLowerCase();
        valB = b.full_name.toLowerCase();
        break;
      case 'role':
        valA = (a.role ?? '').toLowerCase();
        valB = (b.role ?? '').toLowerCase();
        break;
      case 'museum':
        valA = a.museum_name.toLowerCase();
        valB = b.museum_name.toLowerCase();
        break;
      case 'stage':
        valA = a.museum_stage;
        valB = b.museum_stage;
        break;
      case 'email':
        valA = (a.email ?? '').toLowerCase();
        valB = (b.email ?? '').toLowerCase();
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

const ENGAGEMENT_DOTS: Record<ContactListItem['engagement_level'], string> = {
  active: '#16A34A',
  responded: '#4F46E5',
  outreach: '#2563EB',
  none: '#9CA3AF',
};

export function ContactTable({ contacts, onSelect }: ContactTableProps) {
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

  const sorted = sortContacts(contacts, sortKey, sortDir);

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/40">
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="name" current={sortKey} dir={sortDir} label="Name" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="role" current={sortKey} dir={sortDir} label="Role" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="museum" current={sortKey} dir={sortDir} label="Museum" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="stage" current={sortKey} dir={sortDir} label="Stage" onSort={handleSort} />
            </th>
            <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">
              <SortButton col="email" current={sortKey} dir={sortDir} label="Email" onSort={handleSort} />
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
          {sorted.map((contact) => (
            <tr
              key={contact.id}
              onClick={() => onSelect(contact.id)}
              className={cn(
                'border-b last:border-0 cursor-pointer transition-colors',
                'hover:bg-muted/40'
              )}
            >
              {/* Name + engagement dot */}
              <td className="px-4 py-3 font-medium">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block size-2 rounded-full shrink-0"
                    style={{ backgroundColor: ENGAGEMENT_DOTS[contact.engagement_level] }}
                    title={`Engagement: ${contact.engagement_level}`}
                  />
                  <span className="truncate max-w-[160px]">{contact.full_name}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {contact.role ?? <span className="opacity-40">—</span>}
              </td>
              <td className="px-4 py-3 text-xs max-w-[180px]">
                <span className="truncate block">{contact.museum_name}</span>
              </td>
              <td className="px-4 py-3">
                <StageBadge stage={contact.museum_stage as PipelineStage} size="sm" />
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground max-w-[180px]">
                {contact.email ? (
                  <a
                    href={`mailto:${contact.email}`}
                    onClick={(e) => e.stopPropagation()}
                    className="text-primary hover:underline truncate block"
                  >
                    {contact.email}
                  </a>
                ) : (
                  <span className="opacity-40">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {contact.museum_source ?? <span className="opacity-40">—</span>}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground text-center">
                {contact.interaction_count}
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {formatDateShort(contact.last_interaction)}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={8} className="px-4 py-8 text-center text-muted-foreground text-sm">
                No contacts match the current filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
