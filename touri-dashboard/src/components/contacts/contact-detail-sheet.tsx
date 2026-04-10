'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ExternalLink, Mail, Layers, Brain, CalendarDays, Linkedin } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { StageBadge } from '@/components/pipeline/stage-badge';
import { InteractionTimeline } from '@/components/pipeline/interaction-timeline';
import type { ContactListItem, Interaction, Memory } from '@/lib/types';
import type { PipelineStage } from '@/lib/types';
import { format, parseISO } from 'date-fns';

interface ContactDetailData {
  contact: ContactListItem;
  interactions: (Interaction & { contact_name?: string | null })[];
  memories: Memory[];
}

interface ContactDetailSheetProps {
  contactId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getAvatarColor(source: string | null): string {
  switch (source?.toLowerCase()) {
    case 'hubspot':
      return '#2563EB';
    case 'mailerlite':
      return '#16A34A';
    default:
      return '#6B7280';
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr.slice(0, 10);
  }
}

export function ContactDetailSheet({ contactId, open, onOpenChange }: ContactDetailSheetProps) {
  const router = useRouter();
  const [data, setData] = useState<ContactDetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!contactId || !open) return;

    setLoading(true);
    setError(null);
    setData(null);

    fetch(`/api/contacts/${contactId}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [contactId, open]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-[540px] p-0 flex flex-col gap-0">
        {loading && (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">Loading…</p>
          </div>
        )}

        {error && (
          <div className="flex-1 flex items-center justify-center p-6">
            <p className="text-sm text-destructive">Failed to load contact: {error}</p>
          </div>
        )}

        {!loading && !error && !data && (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">No contact selected.</p>
          </div>
        )}

        {!loading && !error && data && (() => {
          const { contact, interactions, memories } = data;
          const avatarColor = getAvatarColor(contact.museum_source);
          const initials = getInitials(contact.full_name);

          // Filter contact_intel memories for this museum
          const contactMemories = memories.filter(
            (m) => m.type === 'contact_intel' || m.museum_id === contact.museum_id
          );

          // Upcoming follow-ups from interactions
          const today = new Date().toISOString().slice(0, 10);
          const upcomingFollowups = interactions
            .filter((i) => i.follow_up_date && i.follow_up_date >= today)
            .sort((a, b) => (a.follow_up_date ?? '').localeCompare(b.follow_up_date ?? ''));

          return (
            <>
              {/* Header */}
              <SheetHeader className="px-5 pt-5 pb-4 border-b">
                <div className="flex items-start gap-3 pr-8">
                  {/* Avatar */}
                  <div
                    className="size-10 rounded-full flex items-center justify-center text-white text-sm font-semibold shrink-0 select-none"
                    style={{ backgroundColor: avatarColor }}
                  >
                    {initials}
                  </div>

                  <div className="flex-1 min-w-0">
                    <SheetTitle className="text-base leading-snug">{contact.full_name}</SheetTitle>
                    {contact.role && (
                      <SheetDescription className="mt-0.5">{contact.role}</SheetDescription>
                    )}

                    {/* Email + LinkedIn */}
                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                      {contact.email && (
                        <a
                          href={`mailto:${contact.email}`}
                          className="flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          <Mail className="size-3" />
                          {contact.email}
                        </a>
                      )}
                      {contact.linkedin_url && (
                        <a
                          href={contact.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          <Linkedin className="size-3" />
                          LinkedIn
                          <ExternalLink className="size-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </SheetHeader>

              {/* Scrollable body */}
              <ScrollArea className="flex-1">
                <div className="px-5 py-4 space-y-5">

                  {/* Museum section */}
                  <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                      Museum
                    </h3>
                    <div className="p-3 rounded-lg border bg-card space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium">{contact.museum_name}</p>
                        <StageBadge stage={contact.museum_stage as PipelineStage} size="sm" />
                      </div>
                      {(contact.museum_city || contact.museum_country) && (
                        <p className="text-xs text-muted-foreground">
                          {[contact.museum_city, contact.museum_country].filter(Boolean).join(', ')}
                        </p>
                      )}
                      {contact.museum_source && (
                        <p className="text-xs text-muted-foreground">
                          Source: {contact.museum_source}
                        </p>
                      )}
                    </div>
                  </section>

                  <Separator />

                  {/* Interaction Timeline */}
                  <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 flex items-center gap-1.5">
                      <Layers className="size-3.5" />
                      Interactions ({interactions.length})
                    </h3>
                    <InteractionTimeline interactions={interactions} />
                  </section>

                  {/* Memories */}
                  {contactMemories.length > 0 && (
                    <>
                      <Separator />
                      <section>
                        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 flex items-center gap-1.5">
                          <Brain className="size-3.5" />
                          Memories ({contactMemories.length})
                        </h3>
                        <div className="space-y-2">
                          {contactMemories.slice(0, 10).map((m) => (
                            <div key={m.id} className="p-3 rounded-lg border bg-card">
                              <p className="text-xs">{m.content}</p>
                              {m.tags && (
                                <p className="text-[10px] text-muted-foreground mt-1">
                                  {(() => {
                                    try {
                                      const tags = JSON.parse(m.tags) as string[];
                                      return tags.join(' · ');
                                    } catch {
                                      return m.tags;
                                    }
                                  })()}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </section>
                    </>
                  )}

                  {/* Follow-ups */}
                  {upcomingFollowups.length > 0 && (
                    <>
                      <Separator />
                      <section>
                        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 flex items-center gap-1.5">
                          <CalendarDays className="size-3.5" />
                          Upcoming Follow-ups
                        </h3>
                        <div className="space-y-1.5">
                          {upcomingFollowups.map((i) => (
                            <div
                              key={i.id}
                              className="flex items-center justify-between px-3 py-2 rounded-lg border bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-900"
                            >
                              <p className="text-xs text-amber-700 dark:text-amber-400">
                                {i.follow_up_action ?? 'Follow up'}
                              </p>
                              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
                                {formatDate(i.follow_up_date)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </section>
                    </>
                  )}

                </div>
              </ScrollArea>

              {/* Footer actions */}
              <SheetFooter className="border-t px-5 py-3 flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    router.push(`/pipeline?museum=${contact.museum_id}`);
                    onOpenChange(false);
                  }}
                >
                  View in Pipeline
                </Button>
                <Button
                  className="flex-1"
                  variant="default"
                  onClick={() => {
                    const prompt = `Draft email for ${contact.full_name} at ${contact.museum_name}`;
                    router.push(`/chat?prompt=${encodeURIComponent(prompt)}`);
                    onOpenChange(false);
                  }}
                >
                  <Mail className="size-4 mr-2" />
                  Draft Email
                </Button>
              </SheetFooter>
            </>
          );
        })()}
      </SheetContent>
    </Sheet>
  );
}
