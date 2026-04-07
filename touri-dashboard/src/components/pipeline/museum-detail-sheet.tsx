'use client';

import { useEffect, useState } from 'react';
import { ExternalLink, Users, Layers, FlaskConical } from 'lucide-react';
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
import { StageBadge } from './stage-badge';
import { ScoreBadge } from './score-badge';
import { ContactList } from './contact-list';
import { InteractionTimeline } from './interaction-timeline';
import type { Contact, Interaction, Research } from '@/lib/types';
import type { MuseumListItem } from '@/lib/types';
import { cn } from '@/lib/utils';

interface DetailData {
  museum: MuseumListItem;
  contacts: Contact[];
  interactions: (Interaction & { contact_name?: string | null })[];
  research: Research[];
}

interface MuseumDetailSheetProps {
  museumId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <div className="flex gap-2">
      <span className="text-xs text-muted-foreground w-32 shrink-0 mt-0.5">{label}</span>
      <span className="text-xs flex-1">{value}</span>
    </div>
  );
}

export function MuseumDetailSheet({ museumId, open, onOpenChange }: MuseumDetailSheetProps) {
  const [data, setData] = useState<DetailData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!museumId || !open) return;

    setLoading(true);
    setError(null);

    fetch(`/api/leads/${museumId}`)
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
  }, [museumId, open]);

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
            <p className="text-sm text-destructive">Failed to load museum: {error}</p>
          </div>
        )}

        {!loading && !error && !data && (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">No museum selected.</p>
          </div>
        )}

        {!loading && !error && data && (() => {
          const museum = data.museum;
          const locationParts = [museum.city, museum.country].filter(Boolean);
          const location = locationParts.join(', ');

          return (
            <>
              {/* Header */}
              <SheetHeader className="px-5 pt-5 pb-4 border-b">
                <div className="pr-8">
                  <SheetTitle className="text-base leading-snug">{museum.name}</SheetTitle>
                  {location && (
                    <SheetDescription className="mt-0.5">{location}</SheetDescription>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <StageBadge stage={museum.stage} size="md" />
                  {museum.score !== null && <ScoreBadge score={museum.score} />}
                  <span className="text-xs text-muted-foreground ml-auto">
                    Tier {museum.tier}
                  </span>
                </div>
              </SheetHeader>

              {/* Scrollable body */}
              <ScrollArea className="flex-1">
                <div className="px-5 py-4 space-y-5">

                  {/* Museum info grid */}
                  <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                      Details
                    </h3>
                    <div className="space-y-1.5">
                      <InfoRow
                        label="Website"
                        value={
                          museum.website ? (
                            <a
                              href={museum.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline flex items-center gap-1 truncate"
                            >
                              {museum.website.replace(/^https?:\/\//, '')}
                              <ExternalLink className="size-3 shrink-0" />
                            </a>
                          ) : null
                        }
                      />
                      <InfoRow
                        label="Annual visitors"
                        value={
                          museum.annual_visitors
                            ? museum.annual_visitors.toLocaleString()
                            : null
                        }
                      />
                      <InfoRow
                        label="Digital maturity"
                        value={
                          museum.digital_maturity ? (
                            <span className={cn(
                              'capitalize',
                              museum.digital_maturity === 'high' && 'text-green-600',
                              museum.digital_maturity === 'medium' && 'text-amber-600',
                              museum.digital_maturity === 'low' && 'text-red-600',
                            )}>
                              {museum.digital_maturity}
                            </span>
                          ) : null
                        }
                      />
                      <InfoRow label="Audioguide" value={museum.current_audioguide} />
                      <InfoRow label="Source" value={museum.source} />
                      {museum.source_detail && (
                        <InfoRow label="Source detail" value={museum.source_detail} />
                      )}
                    </div>
                  </section>

                  <Separator />

                  {/* Contacts */}
                  <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 flex items-center gap-1.5">
                      <Users className="size-3.5" />
                      Contacts ({data.contacts.length})
                    </h3>
                    <ContactList contacts={data.contacts} />
                  </section>

                  <Separator />

                  {/* Interaction timeline */}
                  <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 flex items-center gap-1.5">
                      <Layers className="size-3.5" />
                      Interactions ({data.interactions.length})
                    </h3>
                    <InteractionTimeline interactions={data.interactions} />
                  </section>

                  <Separator />

                  {/* Research */}
                  <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 flex items-center gap-1.5">
                      <FlaskConical className="size-3.5" />
                      Research
                    </h3>
                    {data.research.length === 0 ? (
                      <div className="py-4 text-center text-sm text-muted-foreground border-2 border-dashed border-border rounded-lg">
                        No research notes yet.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {data.research.map((r) => (
                          <div key={r.id} className="p-3 rounded-lg border bg-card text-xs space-y-1.5">
                            {r.hook_line && (
                              <p className="font-medium">Hook: {r.hook_line}</p>
                            )}
                            {r.insights && (
                              <p className="text-muted-foreground">{r.insights}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </section>

                </div>
              </ScrollArea>

              {/* Footer */}
              <SheetFooter className="border-t px-5 py-3">
                <Button disabled className="w-full" variant="default">
                  Draft Email (coming soon)
                </Button>
              </SheetFooter>
            </>
          );
        })()}
      </SheetContent>
    </Sheet>
  );
}
