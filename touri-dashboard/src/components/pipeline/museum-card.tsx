'use client';

import { cn } from '@/lib/utils';
import { StageBadge } from './stage-badge';
import { ScoreBadge } from './score-badge';
import type { MuseumListItem } from '@/lib/types';

interface MuseumCardProps {
  museum: MuseumListItem;
  onClick: () => void;
  isDragging?: boolean;
}

function getDaysSinceActivity(lastActivity: string | null): string {
  if (!lastActivity) return 'Never contacted';
  const diff = Date.now() - new Date(lastActivity).getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return 'Today';
  if (days === 1) return '1 day ago';
  return `${days}d ago`;
}

function getLocationLine(museum: MuseumListItem): string {
  if (museum.city && museum.country) return `${museum.city}, ${museum.country}`;
  if (museum.country) return museum.country;
  return museum.source ?? 'Unknown source';
}

const TIER_COLORS: Record<number, string> = {
  1: '#F59E0B', // gold
  2: '#9CA3AF', // silver
  3: '#D1D5DB', // muted
};

export function MuseumCard({ museum, onClick, isDragging }: MuseumCardProps) {
  const location = getLocationLine(museum);
  const activityText = getDaysSinceActivity(museum.last_activity);
  const tierColor = TIER_COLORS[museum.tier] ?? TIER_COLORS[3];

  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-card rounded-lg p-3 cursor-grab shadow-sm border transition-all duration-150',
        'hover:border-primary/40 hover:shadow-md',
        isDragging && 'rotate-[2deg] scale-[1.02] shadow-lg border-primary/50'
      )}
    >
      {/* Name */}
      <p className="text-sm font-medium leading-snug line-clamp-2 mb-1.5">
        {museum.name}
      </p>

      {/* Location */}
      <p className="text-xs text-muted-foreground mb-2 truncate">{location}</p>

      {/* Contact */}
      <p className="text-xs text-muted-foreground mb-2">
        {museum.primary_contact_name ?? 'No contact'}
      </p>

      {/* Bottom row: badges + tier dot + activity */}
      <div className="flex items-center justify-between gap-1.5 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          <StageBadge stage={museum.stage} size="sm" />
          {museum.score !== null && <ScoreBadge score={museum.score} />}
          {/* Tier dot */}
          <span
            className="inline-block size-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: tierColor }}
            title={`Tier ${museum.tier}`}
          />
        </div>
        <span className="text-[10px] text-muted-foreground whitespace-nowrap">
          {activityText}
        </span>
      </div>
    </div>
  );
}
