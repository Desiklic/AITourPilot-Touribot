'use client';

import { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  MessageSquare,
  Send,
  Brain,
  Star,
  Telescope,
  Search,
  Zap,
  Cpu,
  Info,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ModelArea {
  key: string;
  label: string;
  description: string;
  icon: string;
  provider: string;
  model: string;
  temperature: number | null;
  max_tokens: number | null;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ICON_MAP: Record<string, LucideIcon> = {
  MessageSquare,
  Send,
  Brain,
  Star,
  Telescope,
  Search,
  Zap,
};

const PROVIDER_STYLES: Record<string, { badge: string; label: string }> = {
  anthropic: {
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    label: 'Anthropic',
  },
  google: {
    badge: 'bg-green-500/20 text-green-400 border-green-500/30',
    label: 'Google',
  },
};

const MODEL_DISPLAY: Record<string, string> = {
  'claude-sonnet-4-6': 'Claude Sonnet 4.6',
  'claude-haiku-4-5-20251001': 'Claude Haiku 4.5',
  'gemini-2.5-pro': 'Gemini 2.5 Pro',
  'gemini-2.5-flash': 'Gemini 2.5 Flash',
};

function getModelDisplayName(id: string): string {
  return MODEL_DISPLAY[id] ?? id;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function AreaCard({ area }: { area: ModelArea }) {
  const IconComponent = ICON_MAP[area.icon] ?? Cpu;
  const providerStyle = PROVIDER_STYLES[area.provider] ?? {
    badge: 'bg-muted text-muted-foreground border-border',
    label: area.provider,
  };

  const hasMeta = area.temperature !== null || area.max_tokens !== null;

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-secondary/30 p-4 hover:bg-secondary/50 transition-colors">
      {/* Header row: icon + label + provider badge */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <IconComponent className="h-4 w-4 text-muted-foreground shrink-0" />
          <span className="text-sm font-semibold truncate">{area.label}</span>
        </div>
        <Badge
          variant="secondary"
          className={`shrink-0 text-[11px] font-medium border ${providerStyle.badge}`}
        >
          {providerStyle.label}
        </Badge>
      </div>

      {/* Description */}
      <p className="text-xs text-muted-foreground leading-snug">{area.description}</p>

      {/* Model name */}
      <p className="text-sm font-medium text-foreground/90">
        {getModelDisplayName(area.model)}
      </p>

      {/* Params row */}
      {hasMeta && (
        <div className="flex items-center gap-3 mt-0.5">
          {area.temperature !== null && (
            <span className="text-[11px] text-muted-foreground">
              temp&nbsp;<span className="text-foreground/70 font-medium">{area.temperature}</span>
            </span>
          )}
          {area.max_tokens !== null && (
            <span className="text-[11px] text-muted-foreground">
              max&nbsp;<span className="text-foreground/70 font-medium">{area.max_tokens.toLocaleString()}</span>&nbsp;tok
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-lg border border-border bg-secondary/30 p-4 space-y-2 animate-pulse">
      <div className="h-4 w-2/3 rounded bg-muted" />
      <div className="h-3 w-full rounded bg-muted" />
      <div className="h-4 w-1/2 rounded bg-muted" />
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ModelsPage() {
  const [areas, setAreas] = useState<ModelArea[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/models')
      .then((res) => res.json())
      .then((data) => {
        setAreas(data.areas ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Split areas into two provider groups for visual grouping
  const anthropicAreas = areas.filter((a) => a.provider === 'anthropic');
  const googleAreas = areas.filter((a) => a.provider === 'google');

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Models</h1>
        <p className="text-muted-foreground text-sm mt-1">
          AI model assigned to each TouriBot functional area.
        </p>
      </div>

      {/* Model Assignments */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <CardTitle>Model Assignments</CardTitle>
          </div>
          <CardDescription>
            Default configuration from <code className="text-xs">args/settings.yaml</code>. Read-only display.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <>
              {/* Anthropic section */}
              {anthropicAreas.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground pl-1">
                    Anthropic
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {anthropicAreas.map((area) => (
                      <AreaCard key={area.key} area={area} />
                    ))}
                  </div>
                </div>
              )}

              {/* Google section */}
              {googleAreas.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground pl-1">
                    Google
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {googleAreas.map((area) => (
                      <AreaCard key={area.key} area={area} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Future enhancements info box */}
      <Card className="border-dashed border-muted-foreground/30">
        <CardContent className="flex items-start gap-3 pt-5 pb-5">
          <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
          <p className="text-sm text-muted-foreground leading-relaxed">
            Model assignments will be editable in a future update. Currently showing default
            configuration from <code className="text-xs">settings.yaml</code>.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
