import { Component } from '@angular/core';

@Component({
  selector: 'app-events',
  standalone: true,
  template: `
    <section class="rounded border border-slate-200 bg-white p-6 text-sm text-slate-600">
      Vista completa del log de eventos en construcción.
    </section>
  `
})
export class EventsComponent {}
