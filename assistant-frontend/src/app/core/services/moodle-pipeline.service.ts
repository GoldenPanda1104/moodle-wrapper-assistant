import { Injectable, NgZone, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';

export interface PipelineEvent {
  event: string;
  message: string;
  level?: string;
  ts?: string;
  url?: string;
}

@Injectable({ providedIn: 'root' })
export class MoodlePipelineService {
  constructor(
    private readonly api: ApiService,
    private readonly zone: NgZone,
  ) {}
  private readonly auth = inject(AuthService);

  runPipeline(kind: string = 'full'): Observable<{ run_id: string }> {
    return this.api.post<{ run_id: string }>(
      `/moodle/pipeline/run?kind=${encodeURIComponent(kind)}`,
      {},
    );
  }

  streamPipeline(runId: string): Observable<PipelineEvent> {
    return new Observable((observer) => {
      const token = this.auth.getAccessToken();
      const url = token
        ? `/api/v1/moodle/pipeline/stream/${runId}?token=${encodeURIComponent(token)}`
        : `/api/v1/moodle/pipeline/stream/${runId}`;
      const source = new EventSource(url);
      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as PipelineEvent;
          this.zone.run(() => observer.next(payload));
        } catch {
          this.zone.run(() => observer.next({ event: 'log', message: event.data }));
        }
      };
      source.onerror = () => {
        source.close();
        this.zone.run(() => observer.error(new Error('Pipeline stream closed.')));
      };
      return () => {
        source.close();
      };
    });
  }
}
