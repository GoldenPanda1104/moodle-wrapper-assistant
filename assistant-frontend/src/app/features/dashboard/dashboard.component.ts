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
import { MoodlePipelineService, PipelineEvent } from '../../core/services/moodle-pipeline.service';
import { MoodleSurveyService } from '../../core/services/moodle-survey.service';
import { MoodleGradeService } from '../../core/services/moodle-grade.service';
import { MoodleSurvey } from '../../core/models/moodle-survey.model';
import { MoodleGradeItem } from '../../core/models/moodle-grade-item.model';
import { MoodleCourse } from '../../core/models/moodle-course.model';

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
  private readonly pipelineService = inject(MoodlePipelineService);
  private readonly surveyService = inject(MoodleSurveyService);
  private readonly gradeService = inject(MoodleGradeService);
  private readonly destroyRef = inject(DestroyRef);

  todayTasks: Task[] = [];
  blockedTasks: Task[] = [];
  pendingSurveys: MoodleSurvey[] = [];
  pendingAssignments: MoodleGradeItem[] = [];
  pendingQuizzes: MoodleGradeItem[] = [];
  recentEvents: EventLog[] = [];
  pipelineLogs: PipelineEvent[] = [];
  pipelineRunId: string | null = null;
  pipelineRunning = false;
  pipelineError: string | null = null;
  pipelineKind: string = 'full';
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

  runPipeline(kind: string = 'full'): void {
    if (this.pipelineRunning) {
      return;
    }
    this.pipelineLogs = [];
    this.pipelineError = null;
    this.pipelineRunId = null;
    this.pipelineKind = kind;
    this.pipelineRunning = true;

    this.pipelineService
      .runPipeline(kind)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ run_id }) => {
          this.pipelineRunId = run_id;
          this.pipelineService
            .streamPipeline(run_id)
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
              next: (entry) => {
                this.pipelineLogs = [...this.pipelineLogs, entry].slice(-200);
                if (entry.event === 'done') {
                  this.pipelineRunning = false;
                }
              },
              error: () => {
                this.pipelineRunning = false;
                this.pipelineError = 'Pipeline stream disconnected.';
              },
            });
        },
        error: () => {
          this.pipelineRunning = false;
          this.pipelineError = 'Unable to start pipeline.';
        },
      });
  }

  private loadData(): void {
    forkJoin({
      tasks: this.taskService.getTasks(),
      events: this.eventService.getRecentEvents(10),
      surveys: this.surveyService.getSurveys(),
      grades: this.gradeService.getGradeItems(),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ tasks, events, surveys, grades }) => {
          this.todayTasks = tasks.filter(
            (task) => task.status === 'ready' || task.status === 'pending'
          );
          this.blockedTasks = tasks.filter((task) => task.status === 'blocked');
          this.recentEvents = events;
          this.pendingSurveys = surveys
            .filter((survey) => !survey.completed_at)
            .sort((a, b) => b.last_seen_at.localeCompare(a.last_seen_at))
            .slice(0, 6);
          const now = new Date();
          const cutoff = new Date(now);
          cutoff.setDate(cutoff.getDate() + 7);
          this.pendingAssignments = grades
            .filter((item) => {
              if (item.item_type !== 'assignment') {
                return false;
              }
              const status = item.submission_status?.toLowerCase() ?? '';
              const notSubmitted = !status.includes('enviado');
              const dueDate = item.due_at ? new Date(item.due_at) : null;
              const withinWindow = dueDate ? dueDate <= cutoff : true;
              return notSubmitted && withinWindow;
            })
            .sort((a, b) => {
              const aDue = a.due_at ? new Date(a.due_at).getTime() : Number.MAX_SAFE_INTEGER;
              const bDue = b.due_at ? new Date(b.due_at).getTime() : Number.MAX_SAFE_INTEGER;
              if (aDue !== bDue) {
                return aDue - bDue;
              }
              return b.last_seen_at.localeCompare(a.last_seen_at);
            })
            .slice(0, 6);
          this.pendingQuizzes = grades
            .filter((item) => {
              if (item.item_type !== 'quiz') {
                return false;
              }
              const dueDate = item.due_at ? new Date(item.due_at) : null;
              const withinWindow = dueDate ? dueDate <= cutoff : true;
              return item.grade_value === null && withinWindow;
            })
            .sort((a, b) => {
              const aDue = a.due_at ? new Date(a.due_at).getTime() : Number.MAX_SAFE_INTEGER;
              const bDue = b.due_at ? new Date(b.due_at).getTime() : Number.MAX_SAFE_INTEGER;
              if (aDue !== bDue) {
                return aDue - bDue;
              }
              return b.last_seen_at.localeCompare(a.last_seen_at);
            })
            .slice(0, 6);
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

  formatCourseName(course?: MoodleCourse | null): string {
    if (!course) {
      return 'Curso';
    }
    return course.name.replace('UDH_B1_', '').split('(')[0].trim();
  }

  formatDueDate(value: string | null): string {
    if (!value) {
      return 'Sin fecha';
    }
    return value;
  }

}
