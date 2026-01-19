import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface PipelineEvent {
  event: string;
  message: string;
  level?: string;
  ts?: string;
  url?: string;
}

@Injectable({ providedIn: 'root' })
export class MoodlePipelineService {
  constructor(private readonly api: ApiService) {}

  runPipeline(): Observable<{ run_id: string }> {
    return this.api.post<{ run_id: string }>('/moodle/pipeline/run', {});
  }

  streamPipeline(runId: string): Observable<PipelineEvent> {
    return new Observable((observer) => {
      const source = new EventSource(`/api/v1/moodle/pipeline/stream/${runId}`);
      source.onmessage = (event) => {
        try {
          observer.next(JSON.parse(event.data) as PipelineEvent);
        } catch {
          observer.next({ event: 'log', message: event.data });
        }
      };
      source.onerror = () => {
        source.close();
        observer.error(new Error('Pipeline stream closed.'));
      };
      return () => {
        source.close();
      };
    });
  }
}
