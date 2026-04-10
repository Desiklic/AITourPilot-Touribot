'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { ContactsToolbar } from './contacts-toolbar';
import { ContactCard } from './contact-card';
import { ContactTable } from './contact-table';
import { ContactDetailSheet } from './contact-detail-sheet';
import type { ContactListItem } from '@/lib/types';

const VIEW_STORAGE_KEY = 'touribot-contacts-view';

interface ContactsPageClientProps {
  initialContacts: ContactListItem[];
}

export function ContactsPageClient({ initialContacts }: ContactsPageClientProps) {
  const [view, setView] = useState<'cards' | 'table'>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(VIEW_STORAGE_KEY);
      if (stored === 'cards' || stored === 'table') return stored;
    }
    return 'cards';
  });
  const [selectedContactId, setSelectedContactId] = useState<number | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [engagementFilter, setEngagementFilter] = useState<string | null>(null);

  // Persist view preference
  useEffect(() => {
    localStorage.setItem(VIEW_STORAGE_KEY, view);
  }, [view]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 200);
    return () => clearTimeout(timer);
  }, [search]);

  // Client-side filtering (76 contacts = instant)
  const filteredContacts = useMemo(() => {
    let result = initialContacts;

    // Text search: name, email, museum name, role
    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase();
      result = result.filter(
        (c) =>
          c.full_name.toLowerCase().includes(q) ||
          (c.email ?? '').toLowerCase().includes(q) ||
          c.museum_name.toLowerCase().includes(q) ||
          (c.role ?? '').toLowerCase().includes(q)
      );
    }

    // Source filter
    if (sourceFilter !== null) {
      result = result.filter(
        (c) => (c.museum_source ?? 'manual').toLowerCase() === sourceFilter
      );
    }

    // Engagement filter
    if (engagementFilter !== null) {
      result = result.filter((c) => c.engagement_level === engagementFilter);
    }

    return result;
  }, [initialContacts, debouncedSearch, sourceFilter, engagementFilter]);

  const handleSelect = useCallback((id: number) => {
    setSelectedContactId(id);
    setSheetOpen(true);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Contacts</h1>
        <p className="text-sm text-muted-foreground">
          {initialContacts.length} contacts across {new Set(initialContacts.map(c => c.museum_id)).size} museums
        </p>
      </div>

      {/* Toolbar */}
      <ContactsToolbar
        view={view}
        onViewChange={setView}
        search={search}
        onSearchChange={setSearch}
        sourceFilter={sourceFilter}
        onSourceFilterChange={setSourceFilter}
        engagementFilter={engagementFilter}
        onEngagementFilterChange={setEngagementFilter}
        resultCount={filteredContacts.length}
        totalCount={initialContacts.length}
      />

      {/* Cards or Table */}
      {view === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredContacts.map((contact) => (
            <ContactCard
              key={contact.id}
              contact={contact}
              onClick={() => handleSelect(contact.id)}
            />
          ))}
          {filteredContacts.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground text-sm border-2 border-dashed border-border rounded-lg">
              No contacts match the current filter.
            </div>
          )}
        </div>
      ) : (
        <ContactTable contacts={filteredContacts} onSelect={handleSelect} />
      )}

      {/* Contact detail sheet */}
      <ContactDetailSheet
        contactId={selectedContactId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
      />
    </div>
  );
}
