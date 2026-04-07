'use client';

import { usePathname } from 'next/navigation';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

function getPageTitle(pathname: string): string {
  const segment = pathname.split('/').filter(Boolean)[0] ?? 'dashboard';
  return segment.charAt(0).toUpperCase() + segment.slice(1);
}

export function Header() {
  const pathname = usePathname();
  const today = format(new Date(), 'EEEE, MMM d');
  const title = getPageTitle(pathname ?? '/');

  return (
    <header className="h-16 border-b border-[var(--border)] flex items-center justify-between px-6">
      <h1 className={cn('text-lg font-semibold text-[var(--foreground)]')}>
        {title}
      </h1>
      <span className="text-sm text-[var(--muted-foreground)]">{today}</span>
    </header>
  );
}
