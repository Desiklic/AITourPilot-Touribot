'use client';

import { useRouter } from 'next/navigation';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
  Cell,
} from 'recharts';

interface StageData {
  stage: number;
  name: string;
  count: number;
  color: string;
}

interface PipelineFunnelProps {
  data: StageData[];
}

interface TooltipPayload {
  payload?: StageData;
  value?: number;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0];
  if (!item?.payload) return null;

  return (
    <div className="rounded-lg border border-border bg-card/95 px-4 py-3 shadow-xl backdrop-blur-sm">
      <p className="text-sm font-semibold text-foreground">{item.payload.name}</p>
      <p className="text-sm text-muted-foreground mt-0.5">
        {item.payload.count} museum{item.payload.count !== 1 ? 's' : ''}
      </p>
    </div>
  );
}

export function PipelineFunnel({ data }: PipelineFunnelProps) {
  const router = useRouter();

  if (!data || data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground text-sm">
        No pipeline data available
      </div>
    );
  }

  // Filter to only stages with museums, sort by stage number
  const filtered = [...data]
    .filter((d) => d.count > 0)
    .sort((a, b) => a.stage - b.stage);

  if (filtered.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground text-sm">
        No museums in pipeline yet
      </div>
    );
  }

  const chartHeight = Math.max(200, filtered.length * 44 + 24);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={filtered}
        layout="vertical"
        margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
        barCategoryGap="20%"
      >
        <XAxis
          type="number"
          allowDecimals={false}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          domain={[0, 'dataMax + 1']}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={120}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
        <Bar
          dataKey="count"
          radius={[0, 4, 4, 0]}
          maxBarSize={32}
          cursor="pointer"
          onClick={(data) => {
            const entry = data as unknown as StageData;
            if (entry?.stage !== undefined) {
              router.push(`/pipeline?stage=${entry.stage}`);
            }
          }}
        >
          <LabelList
            dataKey="count"
            position="right"
            style={{ fill: 'var(--muted-foreground)', fontSize: 12, fontWeight: 600 }}
          />
          {filtered.map((entry) => (
            <Cell key={`cell-${entry.stage}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
