'use client';

import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { StageBadge } from '@/components/pipeline/stage-badge';
import type { MuseumContactGroup } from '@/lib/types';
import type { PipelineStage } from '@/lib/types';

interface MuseumContactCardProps {
  museum: MuseumContactGroup;
  onClick: () => void;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    return format(parseISO(dateStr), 'MMM d');
  } catch {
    return dateStr.slice(0, 10);
  }
}

function getSourceLabel(source: string | null): string {
  if (!source) return 'manual';
  switch (source.toLowerCase()) {
    case 'hubspot':
      return 'HubSpot';
    case 'mailerlite':
      return 'MailerLite';
    default:
      return source;
  }
}

function getAvatarColor(index: number): string {
  const colors = ['#2563EB', '#16A34A', '#9333EA', '#D97706', '#DC2626', '#0891B2'];
  return colors[index % colors.length];
}

export function MuseumContactCard({ museum, onClick }: MuseumContactCardProps) {
  const locationParts = [museum.museum_city, museum.museum_country].filter(Boolean);
  const location = locationParts.join(', ');

  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-card rounded-lg p-4 cursor-pointer border shadow-sm transition-all duration-150',
        'hover:border-primary/40 hover:shadow-md'
      )}
    >
      {/* Header: museum name + stage badge */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <p className="text-sm font-semibold leading-snug flex-1 min-w-0 truncate">
          {museum.museum_name}
        </p>
        <StageBadge stage={museum.museum_stage as PipelineStage} size="sm" />
      </div>

      {/* Location + source */}
      <p className="text-xs text-muted-foreground mb-3">
        {location && <span>{location}</span>}
        {location && museum.museum_source && <span className="mx-1.5 opacity-50">•</span>}
        {museum.museum_source && (
          <span>{getSourceLabel(museum.museum_source)}</span>
        )}
      </p>

      {/* Divider */}
      <div className="border-t mb-3" />

      {/* Contacts list */}
      <div className="space-y-2 mb-3">
        {museum.contacts.map((contact, i) => {
          const initials = getInitials(contact.full_name);
          const avatarColor = getAvatarColor(i);
          return (
            <div key={contact.id} className="flex items-start gap-2">
              <div
                className="size-6 rounded-full flex items-center justify-center text-white text-[9px] font-semibold shrink-0 select-none mt-0.5"
                style={{ backgroundColor: avatarColor }}
              >
                {initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium leading-snug truncate">
                  {contact.full_name}
                  {contact.role && (
                    <span className="font-normal text-muted-foreground"> ({contact.role})</span>
                  )}
                  {contact.is_primary === 1 && (
                    <span className="ml-1 text-[9px] text-primary/70 font-medium">primary</span>
                  )}
                </p>
                {contact.email && (
                  <a
                    href={`mailto:${contact.email}`}
                    onClick={(e) => e.stopPropagation()}
                    className="text-[10px] text-primary hover:underline truncate block"
                  >
                    {contact.email}
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Divider */}
      <div className="border-t mb-2" />

      {/* Footer: interaction count, last activity, follow-up */}
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <span>
            {museum.interaction_count} interaction{museum.interaction_count !== 1 ? 's' : ''}
          </span>
          {museum.last_interaction && (
            <>
              <span className="opacity-50">•</span>
              <span>Last: {formatDate(museum.last_interaction)}</span>
            </>
          )}
        </div>
        {museum.next_followup && (
          <p className="text-[10px] text-amber-600 dark:text-amber-400">
            Follow-up: {formatDate(museum.next_followup)}
          </p>
        )}
      </div>
    </div>
  );
}
