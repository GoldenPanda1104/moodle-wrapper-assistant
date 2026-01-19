import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { MoodleGradeItem } from '../models/moodle-grade-item.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class MoodleGradeService {
  private readonly api = inject(ApiService);

  getGradeItems(courseId?: number): Observable<MoodleGradeItem[]> {
    const params: Record<string, string | number> = {};
    if (courseId !== undefined) {
      params['course_id'] = courseId;
    }
    return this.api.get<MoodleGradeItem[]>('/moodle/grades', params);
  }
}
