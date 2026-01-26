import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { MoodleModule } from '../models/moodle-module.model';

@Injectable({ providedIn: 'root' })
export class MoodleModuleService {
  constructor(private readonly api: ApiService) {}

  getModules(): Observable<MoodleModule[]> {
    return this.api.get<MoodleModule[]>('/moodle/modules');
  }
}
