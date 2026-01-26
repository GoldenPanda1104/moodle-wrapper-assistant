import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MoodleCourse } from '../../core/models/moodle-course.model';
import { MoodleModule } from '../../core/models/moodle-module.model';
import { MoodleModuleService } from '../../core/services/moodle-module.service';

@Component({
  selector: 'app-modules',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf],
  templateUrl: './modules.component.html',
  styleUrl: './modules.component.scss',
})
export class ModulesComponent {
  constructor(
    private readonly moduleService: MoodleModuleService,
    private readonly destroyRef: DestroyRef,
  ) {}

  modules: MoodleModule[] = [];
  filteredModules: MoodleModule[] = [];
  courses: MoodleCourse[] = [];
  isLoading = true;
  lastUpdated: Date | null = null;
  selectedCourseId: number | null = null;

  ngOnInit(): void {
    this.loadModules();
  }

  refresh(): void {
    this.isLoading = true;
    this.loadModules();
  }

  private loadModules(): void {
    this.moduleService
      .getModules()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (modules) => {
          this.modules = modules;
          this.filteredModules = modules;
          this.isLoading = false;
          this.lastUpdated = new Date();
          this.courses = Array.from(
            new Map(
              modules.map((module) => [module.course.id, module.course]),
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

  filterModulesByCourse(courseId: number | null): void {
    this.selectedCourseId = courseId;
    if (courseId === null) {
      this.filteredModules = this.modules;
    } else {
      this.filteredModules = this.modules.filter(
        (module) => module.course.id === courseId,
      );
    }
  }

  toNumber(value: string): number {
    return Number(value);
  }
}
