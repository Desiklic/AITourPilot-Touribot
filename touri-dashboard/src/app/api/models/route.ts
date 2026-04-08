import { NextResponse } from 'next/server';

// GET /api/models
// Returns TouriBot model area definitions.
// Hardcoded defaults from args/settings.yaml — will be dynamic in a future update.
export async function GET() {
  const areas = [
    {
      key: 'chat',
      label: 'Chat',
      description: 'Main conversation with Hermann',
      icon: 'MessageSquare',
      provider: 'anthropic',
      model: 'claude-sonnet-4-6',
      temperature: 0.7,
      max_tokens: 4096,
    },
    {
      key: 'drafting',
      label: 'Email Drafting',
      description: 'Personalized museum outreach emails',
      icon: 'Send',
      provider: 'anthropic',
      model: 'claude-sonnet-4-6',
      temperature: 0.6,
      max_tokens: 2048,
    },
    {
      key: 'memory_extraction',
      label: 'Memory Extraction',
      description: 'Extract facts from conversations',
      icon: 'Brain',
      provider: 'anthropic',
      model: 'claude-haiku-4-5-20251001',
      temperature: 0.3,
      max_tokens: 1024,
    },
    {
      key: 'scoring',
      label: 'Response Scoring',
      description: 'Score inbound email responses 1–5',
      icon: 'Star',
      provider: 'anthropic',
      model: 'claude-sonnet-4-6',
      temperature: null,
      max_tokens: null,
    },
    {
      key: 'deep_research',
      label: 'Deep Research',
      description: 'Multi-pass prospect & museum research',
      icon: 'Telescope',
      provider: 'google',
      model: 'gemini-2.5-pro',
      temperature: 0.7,
      max_tokens: 65536,
    },
    {
      key: 'research',
      label: 'Research',
      description: 'Standard analysis and lookups',
      icon: 'Search',
      provider: 'google',
      model: 'gemini-2.5-pro',
      temperature: null,
      max_tokens: null,
    },
    {
      key: 'fast_research',
      label: 'Fast Research',
      description: 'Quick summaries and fact checks',
      icon: 'Zap',
      provider: 'google',
      model: 'gemini-2.5-flash',
      temperature: null,
      max_tokens: null,
    },
  ];

  return NextResponse.json({ areas }, { headers: { 'Cache-Control': 'no-store' } });
}
