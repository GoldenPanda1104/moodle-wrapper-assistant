import { Component, Input } from '@angular/core';
import { NgClass, NgIf } from '@angular/common';
import { Task } from '../../../core/models/task.model';

@Component({
  selector: 'app-task-card',
  standalone: true,
  imports: [NgClass, NgIf],
  templateUrl: './task-card.component.html',
  styleUrl: './task-card.component.scss'
})
export class TaskCardComponent {
  @Input({ required: true }) task!: Task;

  get priorityBorderClass(): string {
    switch (this.task.priority) {
      case 'critical':
        return 'border-l-red-500';
      case 'high':
        return 'border-l-orange-500';
      case 'medium':
        return 'border-l-yellow-500';
      default:
        return 'border-l-slate-400';
    }
  }

  get priorityBadgeClass(): string {
    switch (this.task.priority) {
      case 'critical':
        return 'border-red-500 text-red-700';
      case 'high':
        return 'border-orange-500 text-orange-700';
      case 'medium':
        return 'border-yellow-500 text-yellow-700';
      default:
        return 'border-slate-400 text-slate-600';
    }
  }
}
