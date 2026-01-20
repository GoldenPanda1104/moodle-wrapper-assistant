import { Injectable, inject } from '@angular/core';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';

export interface VaultStatus {
  has_credentials: boolean;
  cron_enabled: boolean;
}

@Injectable({ providedIn: 'root' })
export class MoodleVaultService {
  private readonly api = inject(ApiService);

  getStatus(): Observable<VaultStatus> {
    return this.api.get<VaultStatus>('/vault/status');
  }

  storeCredentials(payload: { moodle_username: string; moodle_password: string; app_password: string }): Observable<VaultStatus> {
    return this.api.post<VaultStatus>('/vault/store', payload);
  }

  enableCron(appPassword: string): Observable<VaultStatus> {
    return this.api.post<VaultStatus>('/vault/enable-cron', { app_password: appPassword });
  }

  disableCron(): Observable<VaultStatus> {
    return this.api.post<VaultStatus>('/vault/disable-cron', {});
  }
}
