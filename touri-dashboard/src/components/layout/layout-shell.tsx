'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { Sidebar } from './sidebar';
import { Header } from './header';
import { cn } from '@/lib/utils';

// Context so child pages can inject content into the sidebar
const SidebarContentContext = createContext<{
  setSidebarContent: (node: React.ReactNode) => void;
}>({ setSidebarContent: () => {} });

export function useSidebarContent() {
  return useContext(SidebarContentContext);
}

export function LayoutShell({ children }: { children: React.ReactNode }) {
  // Start collapsed on mobile (< 768px), expanded on desktop
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarContent, setSidebarContentRaw] = useState<React.ReactNode>(null);

  // Set initial collapsed state based on viewport width, and listen for resize
  useEffect(() => {
    const checkMobile = () => {
      if (window.innerWidth < 768) {
        setCollapsed(true);
      }
    };
    // Check immediately on mount
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const setSidebarContent = useCallback((node: React.ReactNode) => {
    setSidebarContentRaw(node);
  }, []);

  return (
    <SidebarContentContext.Provider value={{ setSidebarContent }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)}>
        {sidebarContent}
      </Sidebar>
      <div
        className={cn(
          'h-screen flex flex-col transition-all duration-200 overflow-hidden',
          collapsed ? 'ml-[72px]' : 'ml-[260px]'
        )}
      >
        <Header />
        <main className="flex-1 min-h-0 overflow-y-auto p-6">{children}</main>
      </div>
    </SidebarContentContext.Provider>
  );
}
