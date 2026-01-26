import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { EventLog } from '../models/event.model';

@Injectable({ providedIn: 'root' })
export class EventService {
  constructor(private readonly api: ApiService) {}

  getRecentEvents(limit: number): Observable<EventLog[]> {
    return this.api.get<EventLog[]>('/events/', { limit });
  }
}
