import { notFound } from 'next/navigation';
import Link from 'next/link';
import { ChevronRight, ExternalLink } from 'lucide-react';
import { getMuseumDetail } from '@/lib/db/leads-db';
import { StageBadge } from '@/components/pipeline/stage-badge';
import { ScoreBadge } from '@/components/pipeline/score-badge';
import { ContactList } from '@/components/pipeline/contact-list';
import { InteractionTimeline } from '@/components/pipeline/interaction-timeline';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface MuseumDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function MuseumDetailPage({ params }: MuseumDetailPageProps) {
  const { id } = await params;
  const museumId = parseInt(id, 10);
  if (isNaN(museumId)) notFound();

  const detail = getMuseumDetail(museumId);
  if (!detail.museum) notFound();

  const museum = detail.museum;
  const locationParts = [museum.city, museum.country].filter(Boolean);
  const location = locationParts.join(', ');

  return (
    <div className="max-w-3xl mx-auto px-6 py-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-6">
        <Link href="/pipeline" className="hover:text-foreground transition-colors">
          Pipeline
        </Link>
        <ChevronRight className="size-4" />
        <span className="text-foreground font-medium truncate">{museum.name}</span>
      </nav>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold leading-snug mb-1">{museum.name}</h1>
        {location && (
          <p className="text-sm text-muted-foreground">{location}</p>
        )}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <StageBadge stage={museum.stage} size="md" />
          {museum.score !== null && <ScoreBadge score={museum.score} />}
          <span className="text-xs text-muted-foreground">Tier {museum.tier}</span>
        </div>
      </div>

      <Separator className="mb-6" />

      {/* Museum details */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Details
        </h2>
        <dl className="space-y-2">
          {museum.website && (
            <div className="flex gap-3">
              <dt className="text-sm text-muted-foreground w-36 shrink-0">Website</dt>
              <dd>
                <a
                  href={museum.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline flex items-center gap-1"
                >
                  {museum.website.replace(/^https?:\/\//, '')}
                  <ExternalLink className="size-3 shrink-0" />
                </a>
              </dd>
            </div>
          )}
          {museum.annual_visitors && (
            <div className="flex gap-3">
              <dt className="text-sm text-muted-foreground w-36 shrink-0">Annual visitors</dt>
              <dd className="text-sm">{museum.annual_visitors.toLocaleString()}</dd>
            </div>
          )}
          {museum.digital_maturity && (
            <div className="flex gap-3">
              <dt className="text-sm text-muted-foreground w-36 shrink-0">Digital maturity</dt>
              <dd className={cn(
                'text-sm capitalize',
                museum.digital_maturity === 'high' && 'text-green-600',
                museum.digital_maturity === 'medium' && 'text-amber-600',
                museum.digital_maturity === 'low' && 'text-red-600',
              )}>
                {museum.digital_maturity}
              </dd>
            </div>
          )}
          {museum.current_audioguide && (
            <div className="flex gap-3">
              <dt className="text-sm text-muted-foreground w-36 shrink-0">Audioguide</dt>
              <dd className="text-sm">{museum.current_audioguide}</dd>
            </div>
          )}
          {museum.source && (
            <div className="flex gap-3">
              <dt className="text-sm text-muted-foreground w-36 shrink-0">Source</dt>
              <dd className="text-sm">{museum.source}</dd>
            </div>
          )}
        </dl>
      </section>

      <Separator className="mb-6" />

      {/* Contacts */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Contacts ({detail.contacts.length})
        </h2>
        <ContactList contacts={detail.contacts} />
      </section>

      <Separator className="mb-6" />

      {/* Interactions */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
          Interactions ({detail.interactions.length})
        </h2>
        <InteractionTimeline interactions={detail.interactions} />
      </section>

      {detail.research.length > 0 && (
        <>
          <Separator className="mb-6" />
          <section className="mb-6">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
              Research
            </h2>
            <div className="space-y-2">
              {detail.research.map((r) => (
                <div key={r.id} className="p-4 rounded-lg border bg-card space-y-2">
                  {r.hook_line && (
                    <p className="text-sm font-medium">Hook: {r.hook_line}</p>
                  )}
                  {r.insights && (
                    <p className="text-sm text-muted-foreground">{r.insights}</p>
                  )}
                  {r.hypothesis && (
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">Hypothesis:</span> {r.hypothesis}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
