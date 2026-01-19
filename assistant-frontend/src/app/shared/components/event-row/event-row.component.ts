import { Component, Input } from '@angular/core';
import { EventLog } from '../../../core/models/event.model';

@Component({
  selector: 'app-event-row',
  standalone: true,
  templateUrl: './event-row.component.html',
  styleUrl: './event-row.component.scss'
})
export class EventRowComponent {
  @Input({ required: true }) event!: EventLog;

  get relativeTime(): string {
    const created = new Date(this.event.created_at).getTime();
    if (Number.isNaN(created)) {
      return 'sin fecha';
    }
    const now = Date.now();
    const diffMs = Math.max(0, now - created);
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) {
      return 'hace instantes';
    }
    if (diffMinutes < 60) {
      return `hace ${diffMinutes} min`;
    }
    if (diffHours < 24) {
      return `hace ${diffHours} h`;
    }
    return `hace ${diffDays} d`;
  }
}
