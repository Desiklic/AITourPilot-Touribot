import { cn } from '@/lib/utils';
import { STAGE_BY_NUMBER } from '@/lib/constants';
import type { PipelineStage } from '@/lib/types';

interface StageBadgeProps {
  stage: PipelineStage;
  size?: 'sm' | 'md';
}

export function StageBadge({ stage, size = 'md' }: StageBadgeProps) {
  const def = STAGE_BY_NUMBER[stage];
  if (!def) return null;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        size === 'sm' && 'px-2 py-0.5 text-[10px]',
        size === 'md' && 'px-2.5 py-1 text-xs'
      )}
      style={{ backgroundColor: def.bgColor, color: def.color }}
    >
      {def.name}
    </span>
  );
}
