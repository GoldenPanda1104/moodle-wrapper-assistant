import { Component, DestroyRef, inject } from '@angular/core';
import { DatePipe, NgFor, NgIf } from '@angular/common';
import { forkJoin } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TaskService } from '../../core/services/task.service';
import { MoodleGradeService } from '../../core/services/moodle-grade.service';
import { Task } from '../../core/models/task.model';
import { MoodleGradeItem } from '../../core/models/moodle-grade-item.model';

type CalendarItemType = 'assignment' | 'quiz' | 'task';

interface CalendarItem {
  title: string;
  type: CalendarItemType;
  date: Date;
  url?: string | null;
  status?: string;
}

interface CalendarDay {
  date: Date;
  inMonth: boolean;
  isToday: boolean;
  items: CalendarItem[];
}

@Component({
  selector: 'app-calendar',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf],
  templateUrl: './calendar.component.html',
  styleUrl: './calendar.component.scss'
})
export class CalendarComponent {
  private readonly taskService = inject(TaskService);
  private readonly gradeService = inject(MoodleGradeService);
  private readonly destroyRef = inject(DestroyRef);

  viewDate = new Date();
  days: CalendarDay[] = [];
  selectedDate = new Date();
  selectedItems: CalendarItem[] = [];
  isLoading = true;

  ngOnInit(): void {
    this.loadCalendar();
  }

  previousMonth(): void {
    this.viewDate = new Date(this.viewDate.getFullYear(), this.viewDate.getMonth() - 1, 1);
    this.buildCalendar();
  }

  nextMonth(): void {
    this.viewDate = new Date(this.viewDate.getFullYear(), this.viewDate.getMonth() + 1, 1);
    this.buildCalendar();
  }

  selectDay(day: CalendarDay): void {
    this.selectedDate = day.date;
    this.selectedItems = [...day.items].sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  badgeClass(item: CalendarItem): string {
    if (item.type === 'assignment') {
      return 'bg-amber-100 text-amber-700';
    }
    if (item.type === 'quiz') {
      return 'bg-sky-100 text-sky-700';
    }
    return 'bg-emerald-100 text-emerald-700';
  }

  cardClass(item: CalendarItem): string {
    if (item.type === 'assignment') {
      return 'border-amber-200';
    }
    if (item.type === 'quiz') {
      return 'border-sky-200';
    }
    return 'border-emerald-200';
  }

  private loadCalendar(): void {
    forkJoin({
      tasks: this.taskService.getTasks(),
      grades: this.gradeService.getGradeItems()
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ tasks, grades }) => {
          this.items = this.buildItems(tasks, grades);
          this.buildCalendar();
          this.isLoading = false;
        },
        error: () => {
          this.isLoading = false;
        }
      });
  }

  private items: CalendarItem[] = [];

  private buildItems(tasks: Task[], grades: MoodleGradeItem[]): CalendarItem[] {
    const items: CalendarItem[] = [];

    for (const task of tasks) {
      if (!task.deadline) {
        continue;
      }
      items.push({
        title: task.title,
        type: 'task',
        date: new Date(task.deadline),
        status: task.status
      });
    }

    for (const item of grades) {
      const dateValue = item.due_at || item.available_at;
      if (!dateValue) {
        continue;
      }
      const type = item.item_type === 'quiz' ? 'quiz' : 'assignment';
      items.push({
        title: item.title,
        type,
        date: new Date(dateValue),
        url: item.url,
        status: item.submission_status || (item.grade_value === null ? 'pendiente' : 'calificado')
      });
    }

    return items;
  }

  private buildCalendar(): void {
    const year = this.viewDate.getFullYear();
    const month = this.viewDate.getMonth();
    const startOfMonth = new Date(year, month, 1);
    const offset = (startOfMonth.getDay() + 6) % 7;
    const startDate = new Date(year, month, 1 - offset);
    const todayKey = this.toKey(new Date());

    const days: CalendarDay[] = [];
    for (let i = 0; i < 42; i += 1) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      const inMonth = date.getMonth() === month;
      const key = this.toKey(date);
      const items = this.items.filter((item) => this.toKey(item.date) === key);
      days.push({
        date,
        inMonth,
        isToday: key === todayKey,
        items
      });
    }
    this.days = days;
    const selectedKey = this.toKey(this.selectedDate);
    const selectedDay = days.find((day) => this.toKey(day.date) === selectedKey) ?? days.find((day) => day.isToday);
    if (selectedDay) {
      this.selectDay(selectedDay);
    }
  }

  private toKey(date: Date): string {
    return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
  }
}
