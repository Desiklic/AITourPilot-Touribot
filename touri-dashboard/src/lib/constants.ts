import type { PipelineStage } from './types';

export interface StageDefinition {
  stage: PipelineStage;
  name: string;
  meaning: string;
  color: string;
  bgColor: string;
  icon: string;
}

export const PIPELINE_STAGES: StageDefinition[] = [
  { stage: 0, name: 'Identified', meaning: 'Added to database, basic info only', color: '#B8860B', bgColor: '#FEF3C7', icon: 'MapPin' },
  { stage: 1, name: 'Researched', meaning: 'Museum website, LinkedIn, news reviewed', color: '#D97706', bgColor: '#FDE68A', icon: 'Search' },
  { stage: 2, name: 'Personalized', meaning: 'Insight package and hook line ready', color: '#EA580C', bgColor: '#FFEDD5', icon: 'Sparkles' },
  { stage: 3, name: 'Outreach Sent', meaning: 'First email sent', color: '#DC2626', bgColor: '#FEE2E2', icon: 'Send' },
  { stage: 4, name: 'In Sequence', meaning: 'Messages 2 or 3 scheduled or sent', color: '#9333EA', bgColor: '#F3E8FF', icon: 'ListOrdered' },
  { stage: 5, name: 'Responded', meaning: 'Reply received and scored', color: '#2563EB', bgColor: '#DBEAFE', icon: 'MessageCircle' },
  { stage: 6, name: 'Demo Scheduled', meaning: 'Meeting booked', color: '#0891B2', bgColor: '#CFFAFE', icon: 'CalendarCheck' },
  { stage: 7, name: 'Demo Completed', meaning: 'Demo done, follow-up defined', color: '#059669', bgColor: '#D1FAE5', icon: 'Video' },
  { stage: 8, name: 'Proposal Sent', meaning: 'Pilot proposal delivered', color: '#16A34A', bgColor: '#DCFCE7', icon: 'FileText' },
  { stage: 9, name: 'Negotiating', meaning: 'Active deal discussion', color: '#15803D', bgColor: '#BBF7D0', icon: 'Handshake' },
  { stage: 10, name: 'Closed', meaning: 'Won / Lost / Long-term Nurture', color: '#22C55E', bgColor: '#86EFAC', icon: 'Trophy' },
];

export const STAGE_BY_NUMBER = Object.fromEntries(
  PIPELINE_STAGES.map((s) => [s.stage, s])
) as Record<PipelineStage, StageDefinition>;

export interface NavItem {
  label: string;
  route: string;
  icon: string;
  description: string;
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Pipeline', route: '/pipeline', icon: 'Kanban', description: 'Museum leads by pipeline stage' },
  { label: 'Chat', route: '/chat', icon: 'MessageSquare', description: 'Chat with Touri' },
  { label: 'Stats', route: '/stats', icon: 'BarChart2', description: 'Pipeline metrics and funnel' },
  { label: 'Calendar', route: '/calendar', icon: 'Calendar', description: 'Demos and follow-ups' },
  { label: 'Tasks', route: '/tasks', icon: 'CheckSquare', description: 'Pending follow-up actions' },
  { label: 'Memory', route: '/memory', icon: 'Brain', description: "Touri's working memory" },
  { label: 'Settings', route: '/settings', icon: 'Settings', description: 'Preferences and configuration' },
];
