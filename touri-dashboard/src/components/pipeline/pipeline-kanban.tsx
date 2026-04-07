'use client';

import { useState, useEffect } from 'react';
import { DragDropContext, type DropResult } from '@hello-pangea/dnd';
import { PIPELINE_STAGES } from '@/lib/constants';
import { KanbanColumn } from './kanban-column';
import type { MuseumListItem } from '@/lib/types';

interface PipelineKanbanProps {
  museums: MuseumListItem[];
  onSelect: (id: number) => void;
  onStageChange: (museumId: number, newStage: number) => void;
}

export function PipelineKanban({ museums, onSelect, onStageChange }: PipelineKanbanProps) {
  const [mounted, setMounted] = useState(false);

  // Guard against SSR hydration issues with @hello-pangea/dnd
  useEffect(() => { setMounted(true); }, []);

  // Group museums by stage
  const museumsByStage: Record<number, MuseumListItem[]> = {};
  for (const stage of PIPELINE_STAGES) {
    museumsByStage[stage.stage] = [];
  }
  for (const museum of museums) {
    if (museumsByStage[museum.stage]) {
      museumsByStage[museum.stage].push(museum);
    } else {
      museumsByStage[museum.stage] = [museum];
    }
  }

  // Always show stages 0-6; show 7-10 only if they have museums
  const visibleStages = PIPELINE_STAGES.filter(
    (s) => s.stage <= 6 || (museumsByStage[s.stage]?.length ?? 0) > 0
  );

  const handleDragEnd = (result: DropResult) => {
    const { draggableId, source, destination } = result;
    if (!destination) return;

    const sourceStage = parseInt(source.droppableId, 10);
    const destStage = parseInt(destination.droppableId, 10);
    const museumId = parseInt(draggableId, 10);

    if (sourceStage === destStage && source.index === destination.index) return;

    onStageChange(museumId, destStage);
  };

  if (!mounted) return null;

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {visibleStages.map((stage) => (
          <KanbanColumn
            key={stage.stage}
            stage={stage}
            museums={museumsByStage[stage.stage] ?? []}
            onSelect={onSelect}
          />
        ))}
      </div>
    </DragDropContext>
  );
}
