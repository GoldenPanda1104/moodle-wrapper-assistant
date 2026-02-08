import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';

export interface VaultStatus {
  has_credentials: boolean;
  cron_enabled: boolean;
}

@Injectable({ providedIn: 'root' })
export class MoodleVaultService {
  constructor(private readonly api: ApiService) {}

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

  /** Genera una API key para el endpoint de ingest (scraper en casa). Se muestra una sola vez. */
  createIngestKey(): Observable<{ api_key: string; message: string }> {
    return this.api.post<{ api_key: string; message: string }>('/moodle/ingest-key', {});
  }
}
