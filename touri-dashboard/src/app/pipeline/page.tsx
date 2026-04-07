import { getMuseums } from '@/lib/db/leads-db';
import { PipelinePageClient } from '@/components/pipeline/pipeline-page-client';
import type { MuseumListItem } from '@/lib/types';

export default function PipelinePage() {
  const museums = getMuseums() as MuseumListItem[];
  return <PipelinePageClient initialMuseums={museums} />;
}
