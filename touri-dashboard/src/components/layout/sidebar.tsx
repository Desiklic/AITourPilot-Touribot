'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Kanban,
  MessageSquare,
  BarChart2,
  Calendar,
  CheckSquare,
  Brain,
  Settings,
  Landmark,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { icon: Kanban, label: 'Pipeline', href: '/pipeline' },
  { icon: MessageSquare, label: 'Chat', href: '/chat' },
  { icon: BarChart2, label: 'Stats', href: '/stats' },
  { icon: Calendar, label: 'Calendar', href: '/calendar' },
  { icon: CheckSquare, label: 'Tasks', href: '/tasks' },
  { icon: Brain, label: 'Memory', href: '/memory' },
  { icon: Settings, label: 'Settings', href: '/settings' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  /** Slot for page-specific content rendered in the middle area */
  children?: React.ReactNode;
}

export function Sidebar({ collapsed, onToggle, children }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen flex flex-col border-r transition-all duration-200',
        'bg-[var(--sidebar)] border-[var(--sidebar-border)]',
        collapsed ? 'w-[72px]' : 'w-[260px]'
      )}
    >
      {/* Logo + collapse toggle */}
      <div
        className={cn(
          'flex items-center h-16 border-b border-[var(--sidebar-border)]',
          collapsed ? 'px-2 gap-1' : 'px-5 gap-3'
        )}
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--primary)] shrink-0">
          <Landmark className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <span className="text-lg font-semibold text-[var(--sidebar-accent-foreground)] whitespace-nowrap flex-1">
            TouriBot
          </span>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] transition-colors shrink-0"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Nav items */}
      <nav className={cn('flex flex-col gap-1 px-2 py-3', collapsed && 'items-center')}>
        {NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                collapsed && 'justify-center px-0 w-10',
                isActive
                  ? 'bg-[var(--sidebar-accent)] text-[var(--sidebar-accent-foreground)]'
                  : 'text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-accent-foreground)]'
              )}
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Middle area — page-specific content or spacer */}
      {children && !collapsed ? (
        <div className="flex-1 min-h-0 overflow-hidden">{children}</div>
      ) : (
        <div className="flex-1" />
      )}

      {/* Bottom section — Hermann avatar */}
      <div className={cn('px-3 pb-4', collapsed && 'flex justify-center px-0')}>
        <div
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-lg',
            collapsed && 'justify-center px-0'
          )}
        >
          <div className="relative shrink-0">
            <div className="w-10 h-10 rounded-full bg-[var(--primary)] flex items-center justify-center text-sm font-semibold text-white">
              H
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-green-500 border-2 border-[var(--sidebar)]" />
          </div>
          {!collapsed && (
            <div className="min-w-0 text-left">
              <p className="text-sm font-medium text-[var(--sidebar-accent-foreground)] truncate">
                Hermann
              </p>
              <p className="text-xs text-[var(--sidebar-foreground)]">Online</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
