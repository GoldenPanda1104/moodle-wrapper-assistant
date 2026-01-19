import { Component, DestroyRef, inject } from '@angular/core';
import { DatePipe, NgFor, NgIf } from '@angular/common';
import { forkJoin } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TaskService } from '../../core/services/task.service';
import { EventService } from '../../core/services/event.service';
import { Task } from '../../core/models/task.model';
import { EventLog } from '../../core/models/event.model';
import { TaskCardComponent } from '../../shared/components/task-card/task-card.component';
import { EventRowComponent } from '../../shared/components/event-row/event-row.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf, TaskCardComponent, EventRowComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {
  private readonly taskService = inject(TaskService);
  private readonly eventService = inject(EventService);
  private readonly destroyRef = inject(DestroyRef);

  todayTasks: Task[] = [];
  blockedTasks: Task[] = [];
  recentEvents: EventLog[] = [];
  isLoading = true;
  isRefreshing = false;
  lastUpdated: Date | null = null;

  ngOnInit(): void {
    this.loadData();
  }

  refresh(): void {
    this.isRefreshing = true;
    this.loadData();
  }

  private loadData(): void {
    forkJoin({
      tasks: this.taskService.getTasks(),
      events: this.eventService.getRecentEvents(10)
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ tasks, events }) => {
          this.todayTasks = tasks.filter(
            (task) => task.status === 'ready' || task.status === 'pending'
          );
          this.blockedTasks = tasks.filter((task) => task.status === 'blocked');
          this.recentEvents = events;
          this.isLoading = false;
          this.isRefreshing = false;
          this.lastUpdated = new Date();
        },
        error: () => {
          this.isLoading = false;
          this.isRefreshing = false;
        }
      });
  }

}
