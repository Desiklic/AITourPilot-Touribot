import { Suspense } from 'react';
import { getContacts } from '@/lib/db/leads-db';
import { ContactsPageClient } from '@/components/contacts/contacts-page-client';
import type { ContactListItem } from '@/lib/types';

export default function ContactsPage() {
  const contacts = getContacts() as ContactListItem[];
  return (
    <Suspense fallback={
      <div className="space-y-4">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    }>
      <ContactsPageClient initialContacts={contacts} />
    </Suspense>
  );
}
