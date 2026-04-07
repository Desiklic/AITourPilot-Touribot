import { Send, FileText, Clock, TrendingUp } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface EmailData {
  total_sent: number;
  total_drafts: number;
  awaiting_reply: number;
  responses_received: number;
  conversion_rate: number;
}

interface EmailStatsProps {
  data: EmailData;
}

interface StatCardDef {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  accent: string;
  border: string;
  iconBg: string;
}

export function EmailStats({ data }: EmailStatsProps) {
  const conversionPct =
    typeof data.conversion_rate === 'number'
      ? `${(data.conversion_rate * 100).toFixed(1)}%`
      : '0%';

  const cards: StatCardDef[] = [
    {
      label: 'Emails Sent',
      value: data.total_sent ?? 0,
      icon: <Send className="w-4 h-4" />,
      accent: 'from-blue-500/15 to-blue-600/5',
      border: 'border-blue-500/20',
      iconBg: 'bg-blue-500/20 text-blue-400',
    },
    {
      label: 'Drafts Pending',
      value: data.total_drafts ?? 0,
      icon: <FileText className="w-4 h-4" />,
      accent: 'from-amber-500/15 to-amber-600/5',
      border: 'border-amber-500/20',
      iconBg: 'bg-amber-500/20 text-amber-400',
    },
    {
      label: 'Awaiting Reply',
      value: data.awaiting_reply ?? 0,
      icon: <Clock className="w-4 h-4" />,
      accent: 'from-orange-500/15 to-orange-600/5',
      border: 'border-orange-500/20',
      iconBg: 'bg-orange-500/20 text-orange-400',
    },
    {
      label: 'Response Rate',
      value: conversionPct,
      icon: <TrendingUp className="w-4 h-4" />,
      accent: 'from-emerald-500/15 to-emerald-600/5',
      border: 'border-emerald-500/20',
      iconBg: 'bg-emerald-500/20 text-emerald-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map((card) => (
        <Card
          key={card.label}
          className={`relative overflow-hidden border ${card.border} bg-gradient-to-br ${card.accent}`}
        >
          <CardContent className="py-4">
            <div className="flex items-start justify-between mb-3">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider leading-tight">
                {card.label}
              </span>
              <span className={`flex items-center justify-center w-7 h-7 rounded-md ${card.iconBg} flex-shrink-0 ml-2`}>
                {card.icon}
              </span>
            </div>
            <div className="text-2xl font-bold tracking-tight text-foreground">
              {card.value}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
