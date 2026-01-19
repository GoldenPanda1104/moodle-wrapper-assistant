import { DatePipe, NgClass, NgFor, NgIf } from '@angular/common';
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MoodleCourse } from '../../core/models/moodle-course.model';
import { MoodleGradeItem } from '../../core/models/moodle-grade-item.model';
import { MoodleGradeService } from '../../core/services/moodle-grade.service';

@Component({
  selector: 'app-grades',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf, NgClass],
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
            new Map(
              items.map((item) => [item.course.id, item.course]),
            ).values(),
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

  formatItemType(item: MoodleGradeItem): string {
    if (item.item_type === 'assignment') {
      return 'Tarea';
    }
    if (item.item_type === 'quiz') {
      return 'Cuestionario';
    }
    return item.item_type;
  }

  formatAttempts(item: MoodleGradeItem): string {
    if (item.attempts_allowed === null || item.attempts_allowed === undefined) {
      return 'Intentos: -';
    }
    return `Intentos: ${item.attempts_allowed}`;
  }

  formatTimeLimit(item: MoodleGradeItem): string {
    if (!item.time_limit_minutes) {
      return 'Tiempo: -';
    }
    return `Tiempo: ${item.time_limit_minutes} min`;
  }

  formatGradeColor(item: MoodleGradeItem): string {
    if (item.grade_value === null || item.grade_value === undefined) {
      return 'zinc-500';
    }
    if (item.grade_value >= 90) {
      return 'green-500';
    }
    if (item.grade_value >= 70) {
      return 'yellow-500';
    }
    return 'red-500';
  }

  gradeBadgeClasses(item: MoodleGradeItem): string {
    const isMissing =
      item.grade_value === null || item.grade_value === undefined;
    const isHigh = !isMissing && item.grade_value! >= 90;
    const isMid =
      !isMissing && item.grade_value! < 90 && item.grade_value! >= 70;
    const isLow = !isMissing && item.grade_value! < 70;

    if (isMissing) {
      return 'bg-zinc-500 text-white';
    }
    if (isHigh) {
      return 'bg-emerald-500 text-white';
    }
    if (isMid) {
      return 'bg-yellow-500 text-slate-900';
    }
    if (isLow) {
      return 'bg-red-500 text-white';
    }
    return 'bg-zinc-500 text-white';
  }
}
