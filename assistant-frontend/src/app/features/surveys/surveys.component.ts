import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MoodleCourse } from '../../core/models/moodle-course.model';
import { MoodleSurvey } from '../../core/models/moodle-survey.model';
import { MoodleSurveyService } from '../../core/services/moodle-survey.service';

@Component({
  selector: 'app-surveys',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf],
  templateUrl: './surveys.component.html',
  styleUrl: './surveys.component.scss',
})
export class SurveysComponent {
  private readonly surveyService = inject(MoodleSurveyService);
  private readonly destroyRef = inject(DestroyRef);

  surveys: MoodleSurvey[] = [];
  isLoading = true;
  lastUpdated: Date | null = null;
  completing = new Set<number>();
  completed = new Set<number>();
  completionErrors = new Map<number, string>();

  ngOnInit(): void {
    this.loadSurveys();
  }

  refresh(): void {
    this.isLoading = true;
    this.loadSurveys();
  }

  completeSurvey(survey: MoodleSurvey): void {
    if (this.completing.has(survey.id)) {
      return;
    }
    this.completionErrors.delete(survey.id);
    this.completing.add(survey.id);
    this.surveyService
      .completeSurvey(survey.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (result) => {
          if (result?.result?.submitted) {
            this.completed.add(survey.id);
          }
          this.completing.delete(survey.id);
        },
        error: () => {
          this.completing.delete(survey.id);
          this.completionErrors.set(survey.id, 'No se pudo completar la encuesta.');
        },
      });
  }

  private loadSurveys(): void {
    this.surveyService
      .getSurveys()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (surveys) => {
          this.surveys = surveys;
          this.isLoading = false;
          this.lastUpdated = new Date();
        },
        error: () => {
          this.isLoading = false;
        },
      });
  }

  formatCourseName(course: MoodleCourse): string {
    return course.name.replace('UDH_B1_', '').split('(')[0].trim();
  }
}
