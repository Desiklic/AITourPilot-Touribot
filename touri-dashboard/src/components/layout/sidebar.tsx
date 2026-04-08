'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Landmark,
  Settings,
  Brain,
  Cpu,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

const USER_MENU_ITEMS = [
  { icon: Settings, label: 'Settings', href: '/settings' },
  { icon: Brain, label: 'Memory', href: '/memory' },
  { icon: Cpu, label: 'Models', href: '/models' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  /** Slot for page-specific content (e.g. chat session list) rendered in the middle area */
  children?: React.ReactNode;
}

export function Sidebar({ collapsed, onToggle, children }: SidebarProps) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

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

      {/* Middle area — page-specific content or spacer */}
      {children && !collapsed ? (
        <div className="flex-1 min-h-0 overflow-hidden">{children}</div>
      ) : (
        <div className="flex-1" />
      )}

      {/* Bottom section with user menu */}
      <div className="px-3 pb-14 relative" ref={menuRef}>
        {/* Popup menu — pops UP from avatar */}
        {menuOpen && (
          <div
            className={cn(
              'absolute bottom-full mb-2 py-1 rounded-lg border z-50',
              'bg-white border-[var(--sidebar-border)] shadow-lg',
              collapsed ? 'left-0 w-[200px]' : 'left-3 right-3'
            )}
          >
            {USER_MENU_ITEMS.map((item) => {
              const isActive =
                pathname === item.href || pathname?.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-[var(--sidebar-accent)] text-[var(--sidebar-accent-foreground)]'
                      : 'text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-accent-foreground)]'
                  )}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        )}

        {/* Hermann avatar button */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-lg w-full transition-colors',
            menuOpen
              ? 'bg-[var(--sidebar-accent)]'
              : 'hover:bg-[var(--sidebar-accent)]',
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
        </button>
      </div>
    </aside>
  );
}
