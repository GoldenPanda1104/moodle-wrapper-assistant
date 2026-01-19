import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ApiService } from './api.service';
import { Task } from '../models/task.model';

@Injectable({ providedIn: 'root' })
export class TaskService {
  private readonly api = inject(ApiService);

  getTasks(): Observable<Task[]> {
    return this.api.get<Task[]>('/tasks/');
  }

  getTasksByStatus(status: Task['status']): Observable<Task[]> {
    return this.getTasks().pipe(
      map((tasks) => tasks.filter((task) => task.status === status))
    );
  }
}
