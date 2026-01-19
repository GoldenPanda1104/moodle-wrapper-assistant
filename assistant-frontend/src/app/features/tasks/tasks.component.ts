import { Component } from '@angular/core';

@Component({
  selector: 'app-tasks',
  standalone: true,
  template: `
    <section class="rounded border border-slate-200 bg-white p-6 text-sm text-slate-600">
      Vista de tareas completa en construcción.
    </section>
  `
})
export class TasksComponent {}
