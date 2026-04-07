'use client';

import React from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import {
  MapPin, Search, Sparkles, Send, ListOrdered, MessageCircle,
  CalendarCheck, Video, FileText, Handshake, Trophy,
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { MuseumCard } from './museum-card';
import type { StageDefinition } from '@/lib/constants';
import type { MuseumListItem } from '@/lib/types';

const STAGE_ICONS: Record<string, React.ElementType> = {
  MapPin, Search, Sparkles, Send, ListOrdered, MessageCircle,
  CalendarCheck, Video, FileText, Handshake, Trophy,
};

interface KanbanColumnProps {
  stage: StageDefinition;
  museums: MuseumListItem[];
  onSelect: (id: number) => void;
}

export function KanbanColumn({ stage, museums, onSelect }: KanbanColumnProps) {
  const Icon = STAGE_ICONS[stage.icon] ?? MapPin;

  return (
    <div className="flex flex-col w-[280px] shrink-0">
      {/* Column header */}
      <div className="flex items-center gap-2 px-2 py-3">
        <Icon className="size-4 shrink-0" style={{ color: stage.color }} />
        <h3 className="text-sm font-semibold truncate flex-1">{stage.name}</h3>
        <span
          className="text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center font-medium"
          style={{ backgroundColor: stage.bgColor, color: stage.color }}
        >
          {museums.length}
        </span>
      </div>

      {/* Droppable area */}
      <Droppable droppableId={String(stage.stage)}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={cn(
              'flex-1 rounded-lg p-1.5 transition-colors duration-200 min-h-[80px]',
              snapshot.isDraggingOver && 'bg-primary/5 ring-1 ring-primary/20'
            )}
          >
            <ScrollArea className="max-h-[calc(100vh-220px)]">
              <div className="flex flex-col gap-2 pr-1">
                {museums.length === 0 ? (
                  <div className="border-2 border-dashed border-border rounded-lg p-4 text-center">
                    <p className="text-xs text-muted-foreground">No museums</p>
                  </div>
                ) : (
                  museums.map((museum, index) => (
                    <Draggable
                      key={museum.id}
                      draggableId={String(museum.id)}
                      index={index}
                    >
                      {(dragProvided, dragSnapshot) => (
                        <div
                          ref={dragProvided.innerRef}
                          {...dragProvided.draggableProps}
                          {...dragProvided.dragHandleProps}
                        >
                          <MuseumCard
                            museum={museum}
                            onClick={() => onSelect(museum.id)}
                            isDragging={dragSnapshot.isDragging}
                          />
                        </div>
                      )}
                    </Draggable>
                  ))
                )}
                {provided.placeholder}
              </div>
            </ScrollArea>
          </div>
        )}
      </Droppable>
    </div>
  );
}
