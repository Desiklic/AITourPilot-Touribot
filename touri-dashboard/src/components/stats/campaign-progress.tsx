import { Calendar, Building2, Users, Activity } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface CampaignData {
  start_date: string | null;
  days_running: number;
  avg_interactions_per_day: number;
  museums_contacted: number;
  velocity: number;
  total_museums: number;
  contacts_total: number;
  contacts_with_email: number;
}

interface CampaignProgressProps {
  data: CampaignData;
}

interface CampaignCardDef {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  accent: string;
  border: string;
  iconBg: string;
}

export function CampaignProgress({ data }: CampaignProgressProps) {
  const avgPerDay =
    typeof data.avg_interactions_per_day === 'number'
      ? data.avg_interactions_per_day.toFixed(1)
      : '0.0';

  const startDateLabel = data.start_date
    ? new Date(data.start_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '—';

  const cards: CampaignCardDef[] = [
    {
      label: 'Days Active',
      value: data.days_running ?? 0,
      sub: `Since ${startDateLabel}`,
      icon: <Calendar className="w-4 h-4" />,
      accent: 'from-violet-500/15 to-violet-600/5',
      border: 'border-violet-500/20',
      iconBg: 'bg-violet-500/20 text-violet-400',
    },
    {
      label: 'Museums Contacted',
      value: data.museums_contacted ?? 0,
      sub: `of ${data.total_museums ?? 0} total`,
      icon: <Building2 className="w-4 h-4" />,
      accent: 'from-blue-500/15 to-blue-600/5',
      border: 'border-blue-500/20',
      iconBg: 'bg-blue-500/20 text-blue-400',
    },
    {
      label: 'Total Contacts',
      value: data.contacts_total ?? 0,
      sub: `${data.contacts_with_email ?? 0} with email`,
      icon: <Users className="w-4 h-4" />,
      accent: 'from-emerald-500/15 to-emerald-600/5',
      border: 'border-emerald-500/20',
      iconBg: 'bg-emerald-500/20 text-emerald-400',
    },
    {
      label: 'Interactions / Day',
      value: avgPerDay,
      sub: `Velocity: ${typeof data.velocity === 'number' ? data.velocity.toFixed(1) : '0'}`,
      icon: <Activity className="w-4 h-4" />,
      accent: 'from-amber-500/15 to-amber-600/5',
      border: 'border-amber-500/20',
      iconBg: 'bg-amber-500/20 text-amber-400',
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
              <span
                className={`flex items-center justify-center w-7 h-7 rounded-md ${card.iconBg} flex-shrink-0 ml-2`}
              >
                {card.icon}
              </span>
            </div>
            <div className="text-2xl font-bold tracking-tight text-foreground">
              {card.value}
            </div>
            {card.sub && (
              <p className="mt-1 text-xs text-muted-foreground">{card.sub}</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
