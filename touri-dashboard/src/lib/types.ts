// Pipeline stage type
export type PipelineStage = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export interface Museum {
  id: number;
  name: string;
  city: string | null;
  country: string | null;
  country_code: string | null;
  website: string | null;
  annual_visitors: number | null;
  current_audioguide: string | null;
  digital_maturity: 'high' | 'medium' | 'low' | null;
  tier: 1 | 2 | 3;
  source: string | null;
  source_detail: string | null;
  stage: PipelineStage;
  stage_updated_at: string | null;
  score: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Contact {
  id: number;
  museum_id: number;
  first_name: string | null;
  last_name: string | null;
  full_name: string;
  role: string | null;
  email: string | null;
  linkedin_url: string | null;
  preferred_language: string;
  notes: string | null;
  is_primary: 0 | 1;
  created_at: string;
}

export interface Interaction {
  id: number;
  museum_id: number;
  contact_id: number | null;
  direction: 'outbound' | 'inbound';
  channel: 'email' | 'linkedin' | 'phone' | string;
  subject: string | null;
  body: string;
  sequence_step: number | null;
  response_score: number | null;
  sent_at: string | null;
  created_at: string;
  is_draft: 0 | 1;
  event_type: string | null;
  attachments: string | null;
  outcome: string | null;
  follow_up_date: string | null;
  follow_up_action: string | null;
}

export interface Research {
  id: number;
  museum_id: number;
  insights: string | null;
  hypothesis: string | null;
  hook_line: string | null;
  conversation_starter: string | null;
  sources: string | null;
  created_at: string;
  is_current: 0 | 1;
}

export interface Memory {
  id: number;
  content: string;
  type: string;  // contact_intel | museum_intel | interaction | strategy | research | general | fact | insight | event | error
  importance: number;
  museum_id: number | null;     // FK to leads.db museums
  tags: string | null;          // JSON array string
  source: string | null;        // extraction | manual | research | cli
  created_at: string;
  updated_at: string;
}

export interface PipelineStats {
  total_museums: number;
  by_stage: Record<PipelineStage, number>;
  awaiting_reply: number;
  stale_count: number;
  follow_ups_due: number;
  demos_this_week: number;
  closed_won: number;
  avg_days_to_respond: number | null;
}

// Museum with related data for detail views
export interface MuseumDetail extends Museum {
  contacts: Contact[];
  interactions: Interaction[];
  research: Research[];
}

// Museum list item returned by /api/leads (Museum + joined fields)
export interface MuseumListItem extends Museum {
  primary_contact_name: string | null;
  primary_contact_email: string | null;
  last_activity: string | null;
}

// Calendar event (follow-up or demo)
export interface CalendarEvent {
  id: number;
  museum_id: number;
  museum_name: string;
  follow_up_date: string;
  follow_up_action: string | null;
  event_type: string | null;
  stage: number;
  type: 'follow_up' | 'demo'; // derived
}

// Contact list item returned by /api/contacts (Contact + joined museum fields + derived stats)
export interface ContactListItem {
  id: number;
  full_name: string;
  role: string | null;
  email: string | null;
  linkedin_url: string | null;
  preferred_language: string;
  is_primary: 0 | 1;
  created_at: string;
  // Joined museum fields
  museum_id: number;
  museum_name: string;
  museum_stage: number;
  museum_source: string | null;
  museum_city: string | null;
  museum_country: string | null;
  museum_website: string | null;
  museum_tier: number;
  museum_score: number | null;
  // Derived
  interaction_count: number;
  last_interaction: string | null;
  next_followup: string | null;
  engagement_level: 'none' | 'outreach' | 'responded' | 'active';
}

// Museum group for the Museums view in Contacts page
export interface MuseumContactGroup {
  museum_id: number;
  museum_name: string;
  museum_city: string | null;
  museum_country: string | null;
  museum_source: string | null;
  museum_stage: number;
  museum_tier: number;
  museum_score: number | null;
  interaction_count: number;
  last_interaction: string | null;
  next_followup: string | null;
  contacts: Array<{
    id: number;
    full_name: string;
    role: string | null;
    email: string | null;
    is_primary: 0 | 1;
  }>;
}

// Follow-up task for the task board
export interface FollowUpTask {
  id: number;
  museum_id: number;
  museum_name: string;
  follow_up_date: string;
  follow_up_action: string | null;
  event_type: string | null;
  outcome: string | null;
  stage: number;
  city: string | null;
  country: string | null;
}
