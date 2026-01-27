import { Component } from '@angular/core';

@Component({
  selector: 'app-events',
  standalone: true,
  template: `
    <section class="space-y-6">
      <header class="flex flex-col gap-3 border-b border-slate-200 pb-4">
        <div class="text-[12px] uppercase tracking-[0.3em] text-slate-400">Event Log</div>
        <h1 class="text-2xl font-semibold text-slate-900">Eventos</h1>
        <p class="text-sm text-slate-500">
          Auditoria de acciones, cambios en Moodle y automatizaciones del sistema.
        </p>
      </header>
      <div class="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-xs font-semibold text-slate-600">
          EV
        </div>
        <h2 class="mt-4 text-lg font-semibold text-slate-900">Vista en preparación</h2>
        <p class="mt-2 text-sm text-slate-500">
          Pronto podrás filtrar eventos por tipo, origen y prioridad.
        </p>
      </div>
    </section>
  `
})
export class EventsComponent {}
