import { cn } from '@/lib/utils';
import type { Contact } from '@/lib/types';

interface ContactListProps {
  contacts: Contact[];
}

function getInitial(contact: Contact): string {
  if (contact.first_name) return contact.first_name.charAt(0).toUpperCase();
  if (contact.full_name) return contact.full_name.charAt(0).toUpperCase();
  return '?';
}

export function ContactList({ contacts }: ContactListProps) {
  if (!contacts || contacts.length === 0) {
    return (
      <div className="py-4 text-center text-sm text-muted-foreground border-2 border-dashed border-border rounded-lg">
        No contacts on record.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {contacts.map((contact) => (
        <div
          key={contact.id}
          className="flex items-start gap-3 p-3 rounded-lg border bg-card"
        >
          {/* Avatar */}
          <div className="size-8 rounded-full bg-primary/15 flex items-center justify-center text-sm font-semibold text-primary shrink-0">
            {getInitial(contact)}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium">{contact.full_name}</span>
              {contact.is_primary === 1 && (
                <span className="text-[10px] rounded-full px-1.5 py-0.5 bg-primary/10 text-primary font-medium">
                  Primary
                </span>
              )}
            </div>
            {contact.role && (
              <p className="text-xs text-muted-foreground mt-0.5">{contact.role}</p>
            )}
            {contact.email && (
              <a
                href={`mailto:${contact.email}`}
                className="text-xs text-primary hover:underline mt-0.5 block truncate"
              >
                {contact.email}
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
