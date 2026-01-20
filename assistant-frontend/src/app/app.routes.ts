import { Routes } from '@angular/router';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { TasksComponent } from './features/tasks/tasks.component';
import { EventsComponent } from './features/events/events.component';
import { CoursesComponent } from './features/courses/courses.component';
import { ModulesComponent } from './features/modules/modules.component';
import { SurveysComponent } from './features/surveys/surveys.component';
import { GradesComponent } from './features/grades/grades.component';
import { LoginComponent } from './features/auth/login.component';
import { RegisterComponent } from './features/auth/register.component';
import { SettingsComponent } from './features/settings/settings.component';
import { CalendarComponent } from './features/calendar/calendar.component';
import { authGuard } from './core/services/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: '', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'tasks', component: TasksComponent, canActivate: [authGuard] },
  { path: 'events', component: EventsComponent, canActivate: [authGuard] },
  { path: 'courses', component: CoursesComponent, canActivate: [authGuard] },
  { path: 'modules', component: ModulesComponent, canActivate: [authGuard] },
  { path: 'surveys', component: SurveysComponent, canActivate: [authGuard] },
  { path: 'grades', component: GradesComponent, canActivate: [authGuard] },
  { path: 'calendar', component: CalendarComponent, canActivate: [authGuard] },
  { path: 'settings', component: SettingsComponent, canActivate: [authGuard] }
];
