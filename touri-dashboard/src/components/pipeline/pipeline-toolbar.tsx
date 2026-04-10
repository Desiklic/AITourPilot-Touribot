'use client';

import { Kanban, Table2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PIPELINE_STAGES } from '@/lib/constants';

interface PipelineToolbarProps {
  view: 'kanban' | 'table';
  onViewChange: (v: 'kanban' | 'table') => void;
  stageFilter: number | null;
  onStageFilterChange: (s: number | null) => void;
  stageCounts: Record<number, number>;
}

export function PipelineToolbar({
  view,
  onViewChange,
  stageFilter,
  onStageFilterChange,
  stageCounts,
}: PipelineToolbarProps) {
  // Always show stages 0-6, plus any higher stages that are populated
  const visibleStages = PIPELINE_STAGES.filter(
    (s) => s.stage <= 6 || (stageCounts[s.stage] ?? 0) > 0
  );

  return (
    <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
      {/* Stage filter chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto flex-1 min-w-0 pb-0.5">
        <button
          onClick={() => onStageFilterChange(null)}
          className={cn(
            'shrink-0 inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
            stageFilter === null
              ? 'bg-foreground text-background'
              : 'bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
          )}
        >
          All
          <span className="opacity-70">{Object.values(stageCounts).reduce((a, b) => a + b, 0)}</span>
        </button>

        {visibleStages.map((stage) => {
          const count = stageCounts[stage.stage] ?? 0;
          const isActive = stageFilter === stage.stage;
          return (
            <button
              key={stage.stage}
              onClick={() => onStageFilterChange(isActive ? null : stage.stage)}
              className={cn(
                'shrink-0 inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors'
              )}
              style={
                isActive
                  ? { backgroundColor: stage.color, color: '#fff' }
                  : { backgroundColor: stage.bgColor, color: stage.color }
              }
            >
              {stage.name}
              <span className="opacity-80">{count}</span>
            </button>
          );
        })}
      </div>

      {/* View toggle */}
      <div className="flex items-center rounded-lg border p-0.5 shrink-0">
        <button
          onClick={() => onViewChange('kanban')}
          className={cn(
            'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
            view === 'kanban'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          )}
          title="Kanban view"
        >
          <Kanban className="size-3.5" />
          <span>Kanban</span>
        </button>
        <button
          onClick={() => onViewChange('table')}
          className={cn(
            'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
            view === 'table'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          )}
          title="Table view"
        >
          <Table2 className="size-3.5" />
          <span>Table</span>
        </button>
      </div>
    </div>
  );
}
