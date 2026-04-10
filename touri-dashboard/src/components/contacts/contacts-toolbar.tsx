'use client';

import { LayoutGrid, Table2, Users, Building2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ContactsToolbarProps {
  entityView: 'people' | 'museums';
  onEntityViewChange: (v: 'people' | 'museums') => void;
  view: 'cards' | 'table';
  onViewChange: (v: 'cards' | 'table') => void;
  search: string;
  onSearchChange: (s: string) => void;
  sourceFilter: string | null;
  onSourceFilterChange: (s: string | null) => void;
  engagementFilter: string | null;
  onEngagementFilterChange: (e: string | null) => void;
  resultCount: number;
  totalCount: number;
}

const SOURCE_CHIPS = [
  { label: 'All', value: null },
  { label: 'HubSpot', value: 'hubspot' },
  { label: 'MailerLite', value: 'mailerlite' },
  { label: 'Manual', value: 'manual' },
] as const;

const ENGAGEMENT_CHIPS = [
  { label: 'All', value: null },
  { label: 'Active', value: 'active' },
  { label: 'Outreach', value: 'outreach' },
  { label: 'Responded', value: 'responded' },
  { label: 'Not contacted', value: 'none' },
] as const;

export function ContactsToolbar({
  entityView,
  onEntityViewChange,
  view,
  onViewChange,
  search,
  onSearchChange,
  sourceFilter,
  onSourceFilterChange,
  engagementFilter,
  onEngagementFilterChange,
  resultCount,
  totalCount,
}: ContactsToolbarProps) {
  const entityLabel = entityView === 'people' ? 'contacts' : 'museums';

  return (
    <div className="flex flex-col gap-3 mb-4">
      {/* Row 1: search + entity toggle + view toggle */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={
              entityView === 'people'
                ? 'Search name, email, museum, role…'
                : 'Search museum name, city, contacts…'
            }
            className={cn(
              'w-full rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1'
            )}
          />
        </div>

        {/* Result count badge */}
        <span className="text-xs text-muted-foreground shrink-0">
          {resultCount === totalCount ? (
            <>{totalCount} {entityLabel}</>
          ) : (
            <>{resultCount} of {totalCount}</>
          )}
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Entity toggle: People / Museums */}
        <div className="flex items-center rounded-lg border p-0.5 shrink-0">
          <button
            onClick={() => onEntityViewChange('people')}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
              entityView === 'people'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
            title="People view"
          >
            <Users className="size-3.5" />
            <span>People</span>
          </button>
          <button
            onClick={() => onEntityViewChange('museums')}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
              entityView === 'museums'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
            title="Museums view"
          >
            <Building2 className="size-3.5" />
            <span>Museums</span>
          </button>
        </div>

        {/* View toggle: Cards / Table */}
        <div className="flex items-center rounded-lg border p-0.5 shrink-0">
          <button
            onClick={() => onViewChange('cards')}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
              view === 'cards'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
            title="Card view"
          >
            <LayoutGrid className="size-3.5" />
            <span>Cards</span>
          </button>
          <button
            onClick={() => onViewChange('table')}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
              view === 'table'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
            title="Table view"
          >
            <Table2 className="size-3.5" />
            <span>Table</span>
          </button>
        </div>
      </div>

      {/* Row 2: source + engagement filter chips */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Source filter */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-muted-foreground shrink-0">Source:</span>
          {SOURCE_CHIPS.map((chip) => {
            const isActive = sourceFilter === chip.value;
            return (
              <button
                key={String(chip.value)}
                onClick={() => onSourceFilterChange(isActive && chip.value !== null ? null : chip.value)}
                className={cn(
                  'shrink-0 inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors',
                  isActive
                    ? 'bg-foreground text-background'
                    : 'bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
                )}
              >
                {chip.label}
              </button>
            );
          })}
        </div>

        {/* Engagement filter — only shown in People view */}
        {entityView === 'people' && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs text-muted-foreground shrink-0">Engagement:</span>
            {ENGAGEMENT_CHIPS.map((chip) => {
              const isActive = engagementFilter === chip.value;
              return (
                <button
                  key={String(chip.value)}
                  onClick={() => onEngagementFilterChange(isActive && chip.value !== null ? null : chip.value)}
                  className={cn(
                    'shrink-0 inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors',
                    isActive
                      ? 'bg-foreground text-background'
                      : 'bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
                  )}
                >
                  {chip.label}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
