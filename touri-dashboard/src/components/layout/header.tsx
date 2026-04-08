'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { format } from 'date-fns';
import { MessageCircle, CheckSquare, CalendarDays, Kanban, BarChart2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const HEADER_NAV = [
  { icon: MessageCircle, label: 'Chat', href: '/chat' },
  { icon: CheckSquare, label: 'Tasks', href: '/tasks' },
  { icon: CalendarDays, label: 'Calendar', href: '/calendar' },
  { icon: Kanban, label: 'Pipeline', href: '/pipeline' },
  { icon: BarChart2, label: 'Stats', href: '/stats' },
];

export function Header() {
  const pathname = usePathname();
  const today = format(new Date(), 'EEEE, MMM d');

  return (
    <header className="h-16 border-b border-[var(--border)] flex items-center justify-between px-6">
      <nav className="flex items-center gap-1">
        {HEADER_NAV.map((item) => {
          const isActive =
            pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[var(--accent)] text-[var(--foreground)]'
                  : 'text-[var(--muted-foreground)] hover:bg-[var(--accent)] hover:text-[var(--foreground)]'
              )}
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <span className="text-sm text-[var(--muted-foreground)]">{today}</span>
    </header>
  );
}
