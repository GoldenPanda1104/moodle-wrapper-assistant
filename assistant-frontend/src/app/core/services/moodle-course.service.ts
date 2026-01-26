import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { MoodleCourse } from '../models/moodle-course.model';

@Injectable({ providedIn: 'root' })
export class MoodleCourseService {
  constructor(private readonly api: ApiService) {}

  getCourses(): Observable<MoodleCourse[]> {
    return this.api.get<MoodleCourse[]>('/moodle/courses');
  }

  completeCourseSurveys(courseId: number): Observable<{ detail: string; results: unknown[] }> {
    return this.api.post<{ detail: string; results: unknown[] }>(
      `/moodle/courses/${courseId}/surveys/complete-all`,
      {}
    );
  }
}
