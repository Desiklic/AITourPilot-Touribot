'use client';

import { useState } from 'react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import type { Interaction } from '@/lib/types';

type InteractionWithContact = Interaction & { contact_name?: string | null };

interface InteractionTimelineProps {
  interactions: InteractionWithContact[];
}

const EVENT_TYPE_STYLES: Record<string, { dot: string; label: string }> = {
  email_sent:          { dot: 'bg-blue-500',  label: 'Email Sent' },
  email_draft:         { dot: 'bg-blue-300',  label: 'Draft' },
  meeting_scheduled:   { dot: 'bg-green-500', label: 'Meeting Scheduled' },
  meeting_noshow:      { dot: 'bg-amber-500', label: 'No-show' },
  meeting_completed:   { dot: 'bg-green-600', label: 'Meeting Done' },
  note:                { dot: 'bg-gray-400',  label: 'Note' },
  prep:                { dot: 'bg-gray-400',  label: 'Prep' },
  reply_received:      { dot: 'bg-indigo-500', label: 'Reply' },
};

function getEventStyle(interaction: InteractionWithContact) {
  if (interaction.event_type && EVENT_TYPE_STYLES[interaction.event_type]) {
    return EVENT_TYPE_STYLES[interaction.event_type];
  }
  if (interaction.direction === 'inbound') {
    return { dot: 'bg-indigo-500', label: 'Inbound' };
  }
  return { dot: 'bg-blue-500', label: 'Outbound' };
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr;
  }
}

interface TimelineItemProps {
  interaction: InteractionWithContact;
  isLast: boolean;
}

function TimelineItem({ interaction, isLast }: TimelineItemProps) {
  const [expanded, setExpanded] = useState(false);
  const style = getEventStyle(interaction);
  const dateStr = formatDate(interaction.sent_at ?? interaction.created_at);
  const hasLongBody = interaction.body && interaction.body.length > 200;

  return (
    <div className="flex gap-3">
      {/* Timeline line + dot */}
      <div className="flex flex-col items-center">
        <div className={cn('size-2.5 rounded-full mt-1 shrink-0', style.dot)} />
        {!isLast && <div className="w-px flex-1 bg-border mt-1 mb-1" />}
      </div>

      {/* Content */}
      <div className={cn('flex-1', !isLast && 'pb-4')}>
        <div className="flex items-center justify-between gap-2 mb-0.5">
          <span className="text-xs font-medium">{style.label}</span>
          <span className="text-[10px] text-muted-foreground shrink-0">{dateStr}</span>
        </div>

        {interaction.contact_name && (
          <p className="text-xs text-muted-foreground mb-1">
            {interaction.direction === 'outbound' ? 'To: ' : 'From: '}
            {interaction.contact_name}
          </p>
        )}

        {interaction.subject && (
          <p className="text-xs font-medium text-foreground mb-1 truncate">
            {interaction.subject}
          </p>
        )}

        {interaction.body && (
          <div>
            <p className={cn('text-xs text-muted-foreground', !expanded && 'line-clamp-3')}>
              {interaction.body}
            </p>
            {hasLongBody && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-[10px] text-primary hover:underline mt-0.5"
              >
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        )}

        {interaction.follow_up_date && (
          <div className="mt-1.5 rounded-md bg-amber-50 border border-amber-200 px-2 py-1 dark:bg-amber-950/30 dark:border-amber-900">
            <p className="text-[10px] text-amber-700 dark:text-amber-400">
              Follow-up: {formatDate(interaction.follow_up_date)}
              {interaction.follow_up_action && ` — ${interaction.follow_up_action}`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export function InteractionTimeline({ interactions }: InteractionTimelineProps) {
  if (!interactions || interactions.length === 0) {
    return (
      <div className="py-6 text-center text-sm text-muted-foreground border-2 border-dashed border-border rounded-lg">
        No interactions yet.
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {interactions.map((interaction, idx) => (
        <TimelineItem
          key={interaction.id}
          interaction={interaction}
          isLast={idx === interactions.length - 1}
        />
      ))}
    </div>
  );
}
