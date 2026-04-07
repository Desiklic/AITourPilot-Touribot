'use client';

import { useEffect, useState } from 'react';
import { AppearanceSection } from '@/components/settings/appearance-section';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, Server, FolderOpen, Loader2 } from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SettingsData {
  touribot_home: string | null;
  databases: {
    leads: { museums: number; contacts: number; interactions: number };
    memory: { memories: number };
  };
  api_url: string;
}

// ─── Stat row helper ──────────────────────────────────────────────────────────

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium font-mono">{value}</span>
    </div>
  );
}

// ─── Settings page ────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [data, setData] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/settings');
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch { /* ignore */ } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Appearance */}
      <AppearanceSection />

      {/* TouriBot Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
            <CardTitle>TouriBot Configuration</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading…</span>
            </div>
          ) : (
            <div>
              <StatRow
                label="TOURIBOT_HOME"
                value={data?.touribot_home ?? 'Not configured'}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Database Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <CardTitle>Database Stats</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading…</span>
            </div>
          ) : (
            <div>
              <p className="text-xs text-muted-foreground mb-3 font-semibold uppercase tracking-wide">
                leads.db
              </p>
              <StatRow label="Museums"      value={data?.databases.leads.museums      ?? 0} />
              <StatRow label="Contacts"     value={data?.databases.leads.contacts     ?? 0} />
              <StatRow label="Interactions" value={data?.databases.leads.interactions ?? 0} />
              <p className="text-xs text-muted-foreground mt-4 mb-3 font-semibold uppercase tracking-wide">
                memory.db
              </p>
              <StatRow label="Memories" value={data?.databases.memory.memories ?? 0} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Server */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-muted-foreground" />
            <CardTitle>API Server</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading…</span>
            </div>
          ) : (
            <div>
              <StatRow label="TouriBot API URL" value={data?.api_url ?? 'http://localhost:8765'} />
              <p className="text-xs text-muted-foreground mt-3">
                The TouriBot Python server must be running locally for chat functionality.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
