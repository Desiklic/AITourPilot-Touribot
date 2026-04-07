'use client';

import { useState, useEffect, useCallback } from 'react';
import { PipelineToolbar } from './pipeline-toolbar';
import { PipelineKanban } from './pipeline-kanban';
import { PipelineTable } from './pipeline-table';
import { MuseumDetailSheet } from './museum-detail-sheet';
import type { MuseumListItem } from '@/lib/types';

const VIEW_STORAGE_KEY = 'touribot-pipeline-view';

interface PipelinePageClientProps {
  initialMuseums: MuseumListItem[];
}

export function PipelinePageClient({ initialMuseums }: PipelinePageClientProps) {
  const [museums, setMuseums] = useState<MuseumListItem[]>(initialMuseums);
  const [view, setView] = useState<'kanban' | 'table'>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(VIEW_STORAGE_KEY);
      if (stored === 'kanban' || stored === 'table') return stored;
    }
    return 'kanban';
  });
  const [stageFilter, setStageFilter] = useState<number | null>(null);
  const [selectedMuseumId, setSelectedMuseumId] = useState<number | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  // Persist view preference
  useEffect(() => {
    localStorage.setItem(VIEW_STORAGE_KEY, view);
  }, [view]);

  // Refetch museums from API
  const refetch = useCallback(async () => {
    try {
      const res = await fetch('/api/leads');
      if (res.ok) {
        const json = await res.json();
        setMuseums(json.museums ?? []);
      }
    } catch (err) {
      console.error('[PipelinePageClient] refetch failed', err);
    }
  }, []);

  // Stage change from DnD drag
  const handleStageChange = useCallback(
    async (museumId: number, newStage: number) => {
      // Optimistic update
      setMuseums((prev) =>
        prev.map((m) =>
          m.id === museumId ? { ...m, stage: newStage as MuseumListItem['stage'] } : m
        )
      );

      try {
        const res = await fetch(`/api/leads/${museumId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stage: newStage }),
        });
        if (res.ok) {
          await refetch();
        } else {
          // Revert on failure
          await refetch();
        }
      } catch (err) {
        console.error('[PipelinePageClient] stage change failed', err);
        await refetch();
      }
    },
    [refetch]
  );

  // Select museum and open detail sheet
  const handleSelect = useCallback((id: number) => {
    setSelectedMuseumId(id);
    setSheetOpen(true);
  }, []);

  // Compute stage counts
  const stageCounts: Record<number, number> = {};
  for (const museum of museums) {
    stageCounts[museum.stage] = (stageCounts[museum.stage] ?? 0) + 1;
  }

  // Apply stage filter
  const filteredMuseums =
    stageFilter !== null ? museums.filter((m) => m.stage === stageFilter) : museums;

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Pipeline</h1>
        <p className="text-sm text-muted-foreground">
          {museums.length} museum{museums.length !== 1 ? 's' : ''} tracked
        </p>
      </div>

      {/* Toolbar */}
      <PipelineToolbar
        view={view}
        onViewChange={setView}
        stageFilter={stageFilter}
        onStageFilterChange={setStageFilter}
        stageCounts={stageCounts}
      />

      {/* Board / Table */}
      {view === 'kanban' ? (
        <PipelineKanban
          museums={filteredMuseums}
          onSelect={handleSelect}
          onStageChange={handleStageChange}
        />
      ) : (
        <PipelineTable museums={filteredMuseums} onSelect={handleSelect} />
      )}

      {/* Museum detail sheet */}
      <MuseumDetailSheet
        museumId={selectedMuseumId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
      />
    </div>
  );
}
