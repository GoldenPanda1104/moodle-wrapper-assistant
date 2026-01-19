import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { MoodleModule } from '../models/moodle-module.model';

@Injectable({ providedIn: 'root' })
export class MoodleModuleService {
  private readonly api = inject(ApiService);

  getModules(): Observable<MoodleModule[]> {
    return this.api.get<MoodleModule[]>('/moodle/modules');
  }
}
