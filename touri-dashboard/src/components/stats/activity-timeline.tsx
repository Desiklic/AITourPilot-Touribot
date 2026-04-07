'use client';

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { format, parseISO, isValid } from 'date-fns';

interface TimelineEntry {
  date: string;
  count: number;
  types?: Record<string, number>;
}

interface ActivityTimelineProps {
  data: TimelineEntry[];
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload || !payload.length) return null;

  const total = payload.reduce((sum, p) => sum + (p.value || 0), 0);
  if (total === 0) return null;

  let formattedDate = label ?? '';
  try {
    if (label) {
      const parsed = parseISO(label);
      if (isValid(parsed)) formattedDate = format(parsed, 'EEE, MMM d');
    }
  } catch {
    // keep raw label
  }

  return (
    <div className="rounded-lg border border-border bg-card/95 px-4 py-3 shadow-xl backdrop-blur-sm">
      <p className="mb-2 text-xs font-medium text-muted-foreground">{formattedDate}</p>
      <div className="space-y-1">
        {payload.map((p) =>
          p.value > 0 ? (
            <div key={p.name} className="flex items-center justify-between gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: p.color }} />
                <span className="text-foreground/80 capitalize">{p.name}</span>
              </div>
              <span className="font-mono font-medium text-foreground">{p.value}</span>
            </div>
          ) : null
        )}
      </div>
      {payload.length > 1 && (
        <div className="mt-2 border-t border-border pt-2 flex justify-between text-sm">
          <span className="text-muted-foreground">Total</span>
          <span className="font-mono font-bold text-foreground">{total}</span>
        </div>
      )}
    </div>
  );
}

// Colors for event types
const EVENT_TYPE_COLORS: Record<string, string> = {
  email: '#3b82f6',
  call: '#10b981',
  note: '#f59e0b',
  demo: '#8b5cf6',
  research: '#ec4899',
  reply: '#22d3ee',
  follow_up: '#f97316',
  default: '#b07d56',
};

function getEventColor(type: string): string {
  return EVENT_TYPE_COLORS[type] || EVENT_TYPE_COLORS.default;
}

export function ActivityTimeline({ data }: ActivityTimelineProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-muted-foreground text-sm">
        No activity data available
      </div>
    );
  }

  const { chartData, eventTypes } = useMemo(() => {
    // Collect all event types present
    const typeSet = new Set<string>();
    for (const entry of data) {
      if (entry.types) {
        Object.keys(entry.types).forEach((t) => typeSet.add(t));
      }
    }
    const eventTypes = Array.from(typeSet);

    // If no type breakdown, use total count
    const hasTypes = eventTypes.length > 0;

    const chartData = data.map((entry) => {
      const row: Record<string, unknown> = { date: entry.date };
      if (hasTypes && entry.types) {
        for (const t of eventTypes) {
          row[t] = entry.types[t] ?? 0;
        }
      } else {
        row['interactions'] = entry.count;
      }
      return row;
    });

    return {
      chartData,
      eventTypes: hasTypes ? eventTypes : ['interactions'],
    };
  }, [data]);

  const tickFill = 'var(--muted-foreground)';
  const gridStroke = 'rgba(255,255,255,0.04)';

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart
        data={chartData}
        margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
      >
        <defs>
          {eventTypes.map((type) => (
            <linearGradient key={type} id={`grad-${type}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={getEventColor(type)} stopOpacity={0.3} />
              <stop offset="95%" stopColor={getEventColor(type)} stopOpacity={0.02} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={(d: string) => {
            try {
              const parsed = parseISO(d);
              return isValid(parsed) ? format(parsed, 'MMM d') : d;
            } catch {
              return d;
            }
          }}
          tick={{ fill: tickFill, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: tickFill, fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={28}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.08)', strokeWidth: 1 }} />
        {eventTypes.map((type) => (
          <Area
            key={type}
            type="monotone"
            dataKey={type}
            name={type}
            stackId="activity"
            stroke={getEventColor(type)}
            fill={`url(#grad-${type})`}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
