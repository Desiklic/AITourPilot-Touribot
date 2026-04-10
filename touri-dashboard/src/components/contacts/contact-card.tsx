'use client';

import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { StageBadge } from '@/components/pipeline/stage-badge';
import type { ContactListItem } from '@/lib/types';
import type { PipelineStage } from '@/lib/types';

interface ContactCardProps {
  contact: ContactListItem;
  onClick: () => void;
}

// Avatar color derived from source
function getAvatarColor(source: string | null): string {
  switch (source?.toLowerCase()) {
    case 'hubspot':
      return '#2563EB'; // blue
    case 'mailerlite':
      return '#16A34A'; // green
    default:
      return '#6B7280'; // gray (manual)
  }
}

// Engagement dot color
function getEngagementDot(level: ContactListItem['engagement_level']): string {
  switch (level) {
    case 'active':
      return '#16A34A'; // green
    case 'responded':
      return '#4F46E5'; // indigo
    case 'outreach':
      return '#2563EB'; // blue
    default:
      return '#9CA3AF'; // gray (none)
  }
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

export function ContactCard({ contact, onClick }: ContactCardProps) {
  const avatarColor = getAvatarColor(contact.museum_source);
  const engagementColor = getEngagementDot(contact.engagement_level);
  const initials = getInitials(contact.full_name);

  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-card rounded-lg p-4 cursor-pointer border shadow-sm transition-all duration-150',
        'hover:border-primary/40 hover:shadow-md'
      )}
    >
      {/* Top row: avatar + name + role/museum */}
      <div className="flex items-start gap-3 mb-3">
        {/* Avatar */}
        <div
          className="size-9 rounded-full flex items-center justify-center text-white text-xs font-semibold shrink-0 select-none"
          style={{ backgroundColor: avatarColor }}
        >
          {initials}
        </div>

        {/* Name + role/museum */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold leading-snug truncate">{contact.full_name}</p>
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {contact.role && <span>{contact.role}, </span>}
            <span className="text-primary/80">{contact.museum_name}</span>
          </p>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t mb-3" />

      {/* Stage badge + engagement dot + interaction count */}
      <div className="flex items-center gap-2 mb-2">
        <StageBadge stage={contact.museum_stage as PipelineStage} size="sm" />
        <span
          className="inline-block size-2 rounded-full shrink-0"
          style={{ backgroundColor: engagementColor }}
          title={`Engagement: ${contact.engagement_level}`}
        />
        <span className="text-xs text-muted-foreground">
          {contact.interaction_count} action{contact.interaction_count !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Email */}
      {contact.email && (
        <p className="text-xs mb-1.5">
          <a
            href={`mailto:${contact.email}`}
            onClick={(e) => e.stopPropagation()}
            className="text-primary hover:underline truncate block"
          >
            {contact.email}
          </a>
        </p>
      )}

      {/* Follow-up date */}
      {contact.next_followup && (
        <p className="text-xs text-amber-600 dark:text-amber-400 mb-1.5">
          Follow-up: {formatDate(contact.next_followup)}
        </p>
      )}

      {/* Divider */}
      <div className="border-t mt-2 mb-2" />

      {/* Footer: source, country, last activity */}
      <div className="flex items-center gap-2 text-[10px] text-muted-foreground flex-wrap">
        <span className="bg-secondary rounded px-1.5 py-0.5">
          {getSourceLabel(contact.museum_source)}
        </span>
        {contact.museum_country && (
          <span>{contact.museum_country}</span>
        )}
        {contact.last_interaction && (
          <span className="ml-auto">{formatDate(contact.last_interaction)}</span>
        )}
      </div>
    </div>
  );
}
