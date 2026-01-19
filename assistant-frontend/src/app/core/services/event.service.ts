import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { EventLog } from '../models/event.model';

@Injectable({ providedIn: 'root' })
export class EventService {
  private readonly api = inject(ApiService);

  getRecentEvents(limit: number): Observable<EventLog[]> {
    return this.api.get<EventLog[]>('/events/', { limit });
  }
}
