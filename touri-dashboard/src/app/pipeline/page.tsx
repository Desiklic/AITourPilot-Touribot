import { Suspense } from 'react';
import { getMuseums } from '@/lib/db/leads-db';
import { PipelinePageClient } from '@/components/pipeline/pipeline-page-client';
import type { MuseumListItem } from '@/lib/types';

export default function PipelinePage() {
  const museums = getMuseums() as MuseumListItem[];
  return (
    <Suspense fallback={
      <div className="space-y-4">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    }>
      <PipelinePageClient initialMuseums={museums} />
    </Suspense>
  );
}
