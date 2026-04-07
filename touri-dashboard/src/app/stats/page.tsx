'use client';

import { useState, useEffect } from 'react';
import { PipelineFunnel } from '@/components/stats/pipeline-funnel';
import { EmailStats } from '@/components/stats/email-stats';
import { ActivityTimeline } from '@/components/stats/activity-timeline';
import { CampaignProgress } from '@/components/stats/campaign-progress';

interface StageEntry {
  stage: number;
  name: string;
  count: number;
  color: string;
}

interface TimelineEntry {
  date: string;
  count: number;
  types?: Record<string, number>;
}

interface StatsData {
  pipeline: {
    total_museums: number;
    by_stage: StageEntry[];
    active_museums: number;
  };
  emails: {
    total_sent: number;
    total_drafts: number;
    awaiting_reply: number;
    responses_received: number;
    conversion_rate: number;
  };
  activity: {
    timeline: TimelineEntry[];
    total_interactions: number;
    days_active: number;
  };
  contacts: {
    total: number;
    with_email: number;
    primary_contacts: number;
  };
  campaign: {
    start_date: string | null;
    days_running: number;
    avg_interactions_per_day: number;
    museums_contacted: number;
    velocity: number;
  };
}

export default function StatsPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/stats')
      .then((r) => r.json())
      .then((data: StatsData) => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-6 flex items-center gap-3 text-muted-foreground">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        Loading statistics…
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6 text-muted-foreground">
        Failed to load statistics. Make sure the API server is running.
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Campaign Statistics</h1>

      {/* Campaign overview cards */}
      <CampaignProgress
        data={{
          ...stats.campaign,
          total_museums: stats.pipeline.total_museums,
          contacts_total: stats.contacts.total,
          contacts_with_email: stats.contacts.with_email,
        }}
      />

      {/* Email performance */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Email Performance</h2>
        <EmailStats data={stats.emails} />
      </div>

      {/* Pipeline funnel */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Pipeline Distribution</h2>
        <div className="bg-card rounded-xl border p-4">
          <PipelineFunnel data={stats.pipeline.by_stage} />
        </div>
      </div>

      {/* Activity timeline */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Recent Activity</h2>
        <div className="bg-card rounded-xl border p-4">
          <ActivityTimeline data={stats.activity.timeline} />
        </div>
      </div>
    </div>
  );
}
