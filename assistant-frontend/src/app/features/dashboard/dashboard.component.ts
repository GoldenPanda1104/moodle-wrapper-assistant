import { Component, DestroyRef } from '@angular/core';
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
import { ChartModule } from 'primeng/chart';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DatePipe, NgFor, NgIf, TaskCardComponent, EventRowComponent, ChartModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {
  constructor(
    private readonly taskService: TaskService,
    private readonly eventService: EventService,
    private readonly pipelineService: MoodlePipelineService,
    private readonly surveyService: MoodleSurveyService,
    private readonly gradeService: MoodleGradeService,
    private readonly destroyRef: DestroyRef,
  ) {}

  todayTasks: Task[] = [];
  blockedTasks: Task[] = [];
  pendingSurveys: MoodleSurvey[] = [];
  pendingAssignments: MoodleGradeItem[] = [];
  pendingQuizzes: MoodleGradeItem[] = [];
  upcomingAssignments: MoodleGradeItem[] = [];
  upcomingQuizzes: MoodleGradeItem[] = [];
  recentEvents: EventLog[] = [];
  pipelineLogs: PipelineEvent[] = [];
  pipelineRunId: string | null = null;
  pipelineRunning = false;
  pipelineError: string | null = null;
  pipelineKind: string = 'full';
  isLoading = true;
  isRefreshing = false;
  lastUpdated: Date | null = null;
  chartWorkloadData: object | null = null;
  chartWorkloadOptions: object | null = null;
  chartDistributionData: object | null = null;
  chartDistributionOptions: object | null = null;
  chartDueData: object | null = null;
  chartDueOptions: object | null = null;

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
              return notSubmitted;
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
              return item.grade_value === null;
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
          this.upcomingAssignments = grades
            .filter((item) => {
              if (item.item_type !== 'assignment' || !item.due_at) {
                return false;
              }
              const status = item.submission_status?.toLowerCase() ?? '';
              const notSubmitted = !status.includes('enviado');
              const dueDate = new Date(item.due_at);
              return notSubmitted && dueDate >= now && dueDate <= cutoff;
            })
            .sort((a, b) => new Date(a.due_at!).getTime() - new Date(b.due_at!).getTime())
            .slice(0, 6);
          this.upcomingQuizzes = grades
            .filter((item) => {
              if (item.item_type !== 'quiz' || !item.due_at) {
                return false;
              }
              const dueDate = new Date(item.due_at);
              return item.grade_value === null && dueDate >= now && dueDate <= cutoff;
            })
            .sort((a, b) => new Date(a.due_at!).getTime() - new Date(b.due_at!).getTime())
            .slice(0, 6);
          this.setChartData();
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

  private setChartData(): void {
    const pendingTotal =
      this.pendingSurveys.length +
      this.pendingAssignments.length +
      this.pendingQuizzes.length;
    const upcomingTotal = this.upcomingAssignments.length + this.upcomingQuizzes.length;

    this.chartWorkloadData = {
      labels: ['Encuestas', 'Tareas', 'Quizzes', 'Proximas'],
      datasets: [
        {
          label: 'Pendientes',
          data: [
            this.pendingSurveys.length,
            this.pendingAssignments.length,
            this.pendingQuizzes.length,
            upcomingTotal,
          ],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.15)',
          pointBackgroundColor: '#1d4ed8',
          tension: 0.4,
          fill: true,
        },
      ],
    };
    this.chartWorkloadOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } },
        },
        y: {
          grid: { color: 'rgba(148, 163, 184, 0.2)' },
          ticks: { color: '#94a3b8', font: { size: 11 }, precision: 0 },
        },
      },
    };

    this.chartDistributionData = {
      labels: ['Pendientes', 'Proximas', 'Bloqueadas', 'Hoy'],
      datasets: [
        {
          data: [pendingTotal, upcomingTotal, this.blockedTasks.length, this.todayTasks.length],
          backgroundColor: ['#2563eb', '#22c55e', '#f97316', '#0ea5e9'],
          hoverBackgroundColor: ['#1d4ed8', '#16a34a', '#ea580c', '#0284c7'],
          borderWidth: 0,
        },
      ],
    };
    this.chartDistributionOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#64748b', boxWidth: 10, boxHeight: 10 },
        },
      },
    };

    const nextDays = this.buildNextDays(7);
    const dueCounts = nextDays.map((day) =>
      this.countDueForDate(day.date)
    );
    this.chartDueData = {
      labels: nextDays.map((day) => day.label),
      datasets: [
        {
          label: 'Vencimientos',
          data: dueCounts,
          backgroundColor: 'rgba(37, 99, 235, 0.18)',
          borderColor: '#2563eb',
          borderRadius: 12,
          borderWidth: 1,
        },
      ],
    };
    this.chartDueOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } },
        },
        y: {
          grid: { color: 'rgba(148, 163, 184, 0.2)' },
          ticks: { color: '#94a3b8', font: { size: 11 }, precision: 0 },
        },
      },
    };
  }

  private buildNextDays(days: number): Array<{ date: Date; label: string }> {
    const formatter = new Intl.DateTimeFormat('es', { weekday: 'short', day: 'numeric' });
    return Array.from({ length: days }).map((_, index) => {
      const date = new Date();
      date.setDate(date.getDate() + index);
      return {
        date,
        label: formatter.format(date).replace('.', ''),
      };
    });
  }

  private countDueForDate(date: Date): number {
    const target = date.toDateString();
    const assignments = this.upcomingAssignments.filter((item) =>
      item.due_at ? new Date(item.due_at).toDateString() === target : false
    );
    const quizzes = this.upcomingQuizzes.filter((item) =>
      item.due_at ? new Date(item.due_at).toDateString() === target : false
    );
    return assignments.length + quizzes.length;
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
