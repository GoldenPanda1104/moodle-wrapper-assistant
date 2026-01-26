import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MoodleCourse } from '../../core/models/moodle-course.model';
import { MoodleCourseService } from '../../core/services/moodle-course.service';

@Component({
  selector: 'app-courses',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf],
  templateUrl: './courses.component.html',
  styleUrl: './courses.component.scss',
})
export class CoursesComponent {
  constructor(
    private readonly courseService: MoodleCourseService,
    private readonly destroyRef: DestroyRef,
  ) {}

  courses: MoodleCourse[] = [];
  isLoading = true;
  lastUpdated: Date | null = null;
  completing = new Set<number>();
  completionErrors = new Map<number, string>();

  ngOnInit(): void {
    this.loadCourses();
  }

  refresh(): void {
    this.isLoading = true;
    this.loadCourses();
  }

  completeAllSurveys(course: MoodleCourse): void {
    if (this.completing.has(course.id)) {
      return;
    }
    this.completionErrors.delete(course.id);
    this.completing.add(course.id);
    this.courseService
      .completeCourseSurveys(course.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.completing.delete(course.id);
        },
        error: () => {
          this.completing.delete(course.id);
          this.completionErrors.set(
            course.id,
            'No se pudieron completar las encuestas.',
          );
        },
      });
  }

  private loadCourses(): void {
    this.courseService
      .getCourses()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (courses) => {
          this.courses = courses;
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
