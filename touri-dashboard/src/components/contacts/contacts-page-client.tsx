'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { ContactsToolbar } from './contacts-toolbar';
import { ContactCard } from './contact-card';
import { ContactTable } from './contact-table';
import { ContactDetailSheet } from './contact-detail-sheet';
import { MuseumContactCard } from './museum-contact-card';
import { MuseumContactTable } from './museum-contact-table';
import { MuseumDetailSheet } from '@/components/pipeline/museum-detail-sheet';
import type { ContactListItem, MuseumContactGroup } from '@/lib/types';

const VIEW_STORAGE_KEY = 'touribot-contacts-view';
const ENTITY_STORAGE_KEY = 'touribot-contacts-entity';

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

  const [entityView, setEntityView] = useState<'people' | 'museums'>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(ENTITY_STORAGE_KEY);
      if (stored === 'people' || stored === 'museums') return stored;
    }
    return 'people';
  });

  const [selectedContactId, setSelectedContactId] = useState<number | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  const [selectedMuseumId, setSelectedMuseumId] = useState<number | null>(null);
  const [museumSheetOpen, setMuseumSheetOpen] = useState(false);

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [engagementFilter, setEngagementFilter] = useState<string | null>(null);

  // Persist view preference
  useEffect(() => {
    localStorage.setItem(VIEW_STORAGE_KEY, view);
  }, [view]);

  // Persist entity view preference
  useEffect(() => {
    localStorage.setItem(ENTITY_STORAGE_KEY, entityView);
  }, [entityView]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 200);
    return () => clearTimeout(timer);
  }, [search]);

  // Derive museum groups from contacts (client-side, no API calls)
  const museumGroups = useMemo(() => {
    const map = new Map<number, MuseumContactGroup>();
    for (const contact of initialContacts) {
      if (!map.has(contact.museum_id)) {
        map.set(contact.museum_id, {
          museum_id: contact.museum_id,
          museum_name: contact.museum_name,
          museum_city: contact.museum_city,
          museum_country: contact.museum_country,
          museum_source: contact.museum_source,
          museum_stage: contact.museum_stage,
          museum_tier: contact.museum_tier,
          museum_score: contact.museum_score,
          interaction_count: contact.interaction_count,
          last_interaction: contact.last_interaction,
          next_followup: contact.next_followup,
          contacts: [],
        });
      }
      map.get(contact.museum_id)!.contacts.push({
        id: contact.id,
        full_name: contact.full_name,
        role: contact.role,
        email: contact.email,
        is_primary: contact.is_primary,
      });
    }
    // Sort contacts within each group: primary first, then by name
    for (const group of map.values()) {
      group.contacts.sort((a, b) => {
        if (a.is_primary !== b.is_primary) return b.is_primary - a.is_primary;
        return a.full_name.localeCompare(b.full_name);
      });
    }
    return Array.from(map.values());
  }, [initialContacts]);

  // Client-side filtering for People view
  const filteredContacts = useMemo(() => {
    let result = initialContacts;

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

    if (sourceFilter !== null) {
      result = result.filter(
        (c) => (c.museum_source ?? 'manual').toLowerCase() === sourceFilter
      );
    }

    if (engagementFilter !== null) {
      result = result.filter((c) => c.engagement_level === engagementFilter);
    }

    return result;
  }, [initialContacts, debouncedSearch, sourceFilter, engagementFilter]);

  // Client-side filtering for Museums view
  const filteredMuseums = useMemo(() => {
    let result = museumGroups;

    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase();
      result = result.filter(
        (m) =>
          m.museum_name.toLowerCase().includes(q) ||
          (m.museum_city ?? '').toLowerCase().includes(q) ||
          (m.museum_country ?? '').toLowerCase().includes(q) ||
          (m.museum_source ?? '').toLowerCase().includes(q) ||
          m.contacts.some((c) => c.full_name.toLowerCase().includes(q))
      );
    }

    if (sourceFilter !== null) {
      result = result.filter(
        (m) => (m.museum_source ?? 'manual').toLowerCase() === sourceFilter
      );
    }

    // Engagement filter does not apply to Museums view

    return result;
  }, [museumGroups, debouncedSearch, sourceFilter]);

  const handleSelectContact = useCallback((id: number) => {
    setSelectedContactId(id);
    setSheetOpen(true);
  }, []);

  const handleSelectMuseum = useCallback((id: number) => {
    setSelectedMuseumId(id);
    setMuseumSheetOpen(true);
  }, []);

  const totalMuseums = museumGroups.length;

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Contacts</h1>
        <p className="text-sm text-muted-foreground">
          {initialContacts.length} contacts across {totalMuseums} museums
        </p>
      </div>

      {/* Toolbar */}
      <ContactsToolbar
        entityView={entityView}
        onEntityViewChange={setEntityView}
        view={view}
        onViewChange={setView}
        search={search}
        onSearchChange={setSearch}
        sourceFilter={sourceFilter}
        onSourceFilterChange={setSourceFilter}
        engagementFilter={engagementFilter}
        onEngagementFilterChange={setEngagementFilter}
        resultCount={entityView === 'people' ? filteredContacts.length : filteredMuseums.length}
        totalCount={entityView === 'people' ? initialContacts.length : totalMuseums}
      />

      {/* People or Museums content */}
      {entityView === 'people' ? (
        <>
          {view === 'cards' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredContacts.map((contact) => (
                <ContactCard
                  key={contact.id}
                  contact={contact}
                  onClick={() => handleSelectContact(contact.id)}
                />
              ))}
              {filteredContacts.length === 0 && (
                <div className="col-span-full py-12 text-center text-muted-foreground text-sm border-2 border-dashed border-border rounded-lg">
                  No contacts match the current filter.
                </div>
              )}
            </div>
          ) : (
            <ContactTable contacts={filteredContacts} onSelect={handleSelectContact} />
          )}
        </>
      ) : (
        <>
          {view === 'cards' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMuseums.map((museum) => (
                <MuseumContactCard
                  key={museum.museum_id}
                  museum={museum}
                  onClick={() => handleSelectMuseum(museum.museum_id)}
                />
              ))}
              {filteredMuseums.length === 0 && (
                <div className="col-span-full py-12 text-center text-muted-foreground text-sm border-2 border-dashed border-border rounded-lg">
                  No museums match the current filter.
                </div>
              )}
            </div>
          ) : (
            <MuseumContactTable museums={filteredMuseums} onSelect={handleSelectMuseum} />
          )}
        </>
      )}

      {/* Contact detail sheet */}
      <ContactDetailSheet
        contactId={selectedContactId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
      />

      {/* Museum detail sheet */}
      <MuseumDetailSheet
        museumId={selectedMuseumId}
        open={museumSheetOpen}
        onOpenChange={setMuseumSheetOpen}
      />
    </div>
  );
}
