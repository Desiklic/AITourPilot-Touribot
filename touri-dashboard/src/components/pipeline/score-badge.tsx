import { cn } from '@/lib/utils';

interface ScoreBadgeProps {
  score: number | null;
}

const SCORE_STYLES: Record<number, { bg: string; color: string; label: string }> = {
  1: { bg: '#FEE2E2', color: '#DC2626', label: '1' },
  2: { bg: '#FFEDD5', color: '#EA580C', label: '2' },
  3: { bg: '#FEF3C7', color: '#B45309', label: '3' },
  4: { bg: '#DBEAFE', color: '#2563EB', label: '4' },
  5: { bg: '#DCFCE7', color: '#16A34A', label: '5' },
};

export function ScoreBadge({ score }: ScoreBadgeProps) {
  if (score === null || score === undefined) return null;

  const style = SCORE_STYLES[score];
  if (!style) return null;

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-full px-2 py-0.5 text-[10px] font-semibold tabular-nums'
      )}
      style={{ backgroundColor: style.bg, color: style.color }}
      title={`Engagement score: ${score}/5`}
    >
      {style.label}★
    </span>
  );
}
