import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { MoodleSurvey } from '../models/moodle-survey.model';

@Injectable({ providedIn: 'root' })
export class MoodleSurveyService {
  private readonly api = inject(ApiService);

  getSurveys(): Observable<MoodleSurvey[]> {
    return this.api.get<MoodleSurvey[]>('/moodle/surveys');
  }

  completeSurvey(surveyId: number): Observable<{ detail: string; result?: { submitted: boolean; url: string } }> {
    return this.api.post<{ detail: string; result?: { submitted: boolean; url: string } }>(
      `/moodle/surveys/complete/${surveyId}`,
      {}
    );
  }
}
