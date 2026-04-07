'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Palette } from 'lucide-react';
import { cn } from '@/lib/utils';

const themes = [
  { id: 'dark', label: 'Dark' },
  { id: 'light', label: 'Light' },
  { id: 'system', label: 'System' },
] as const;

export function AppearanceSection() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Palette className="h-4 w-4 text-muted-foreground" />
          <CardTitle>Appearance</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          {themes.map((t) => {
            const isActive = mounted && theme === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={cn(
                  'relative flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors cursor-pointer text-left',
                  isActive
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/40 hover:bg-muted/30'
                )}
              >
                {/* Theme preview block */}
                <div
                  className={cn(
                    'h-16 w-full rounded-md border',
                    t.id === 'dark'
                      ? 'bg-[#0f0f23] border-white/10'
                      : t.id === 'light'
                        ? 'bg-[#f8f7f4] border-black/10'
                        : 'bg-gradient-to-r from-[#0f0f23] to-[#f8f7f4] border-white/10'
                  )}
                />
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{t.label}</span>
                  {isActive && (
                    <span className="h-2 w-2 rounded-full bg-primary" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
