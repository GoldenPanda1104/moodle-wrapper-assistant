import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  NotificationConfig,
  NotificationItem,
  NotificationPreferences,
} from '../models/notification.model';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  constructor(private readonly api: ApiService) {}

  getNotifications(options?: {
    skip?: number;
    limit?: number;
    unread_only?: boolean;
    notification_type?: string;
  }): Observable<NotificationItem[]> {
    return this.api.get<NotificationItem[]>('/notifications/', options ?? {});
  }

  getUnreadCount(): Observable<{ count: number }> {
    return this.api.get<{ count: number }>('/notifications/unread-count');
  }

  markRead(notificationId: number): Observable<NotificationItem> {
    return this.api.post<NotificationItem>(`/notifications/${notificationId}/read`, {});
  }

  markAllRead(): Observable<{ updated: number }> {
    return this.api.post<{ updated: number }>('/notifications/read-all', {});
  }

  getPreferences(): Observable<NotificationPreferences> {
    return this.api.get<NotificationPreferences>('/notifications/preferences');
  }

  updatePreferences(payload: NotificationPreferences): Observable<NotificationPreferences> {
    return this.api.put<NotificationPreferences>('/notifications/preferences', payload);
  }

  getConfig(): Observable<NotificationConfig> {
    return this.api.get<NotificationConfig>('/notifications/config');
  }
}
