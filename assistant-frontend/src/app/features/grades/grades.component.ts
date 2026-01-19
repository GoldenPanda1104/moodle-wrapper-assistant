import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MoodleCourse } from '../../core/models/moodle-course.model';
import { MoodleGradeItem } from '../../core/models/moodle-grade-item.model';
import { MoodleGradeService } from '../../core/services/moodle-grade.service';

@Component({
  selector: 'app-grades',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf],
  templateUrl: './grades.component.html',
  styleUrl: './grades.component.scss',
})
export class GradesComponent {
  private readonly gradeService = inject(MoodleGradeService);
  private readonly destroyRef = inject(DestroyRef);

  gradeItems: MoodleGradeItem[] = [];
  filteredGradeItems: MoodleGradeItem[] = [];
  courses: MoodleCourse[] = [];
  isLoading = true;
  lastUpdated: Date | null = null;
  selectedCourseId: number | null = null;

  ngOnInit(): void {
    this.loadGrades();
  }

  refresh(): void {
    this.isLoading = true;
    this.loadGrades();
  }

  private loadGrades(): void {
    this.gradeService
      .getGradeItems()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (items) => {
          this.gradeItems = items;
          this.filteredGradeItems = items;
          this.isLoading = false;
          this.lastUpdated = new Date();
          this.courses = Array.from(
            new Map(items.map((item) => [item.course.id, item.course])).values(),
          );
        },
        error: () => {
          this.isLoading = false;
        },
      });
  }

  formatCourseName(course: MoodleCourse): string {
    return course.name.replace('UDH_B1_', '').split('(')[0].trim();
  }

  filterGradesByCourse(courseId: number | null): void {
    this.selectedCourseId = courseId;
    if (courseId === null) {
      this.filteredGradeItems = this.gradeItems;
    } else {
      this.filteredGradeItems = this.gradeItems.filter(
        (item) => item.course.id === courseId,
      );
    }
  }

  toNumber(value: string): number {
    return Number(value);
  }

  formatGrade(item: MoodleGradeItem): string {
    if (item.grade_display && item.grade_display.trim()) {
      return item.grade_display;
    }
    return 'Sin calificar';
  }

  formatStatus(value: string | null): string {
    if (!value) {
      return 'Sin estado';
    }
    return value;
  }

  formatDue(item: MoodleGradeItem): string {
    return item.due_at ? item.due_at : '';
  }
}
