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
import { AuthGuard } from './core/services/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: '', component: DashboardComponent, canActivate: [AuthGuard] },
  { path: 'tasks', component: TasksComponent, canActivate: [AuthGuard] },
  { path: 'events', component: EventsComponent, canActivate: [AuthGuard] },
  { path: 'courses', component: CoursesComponent, canActivate: [AuthGuard] },
  { path: 'modules', component: ModulesComponent, canActivate: [AuthGuard] },
  { path: 'surveys', component: SurveysComponent, canActivate: [AuthGuard] },
  { path: 'grades', component: GradesComponent, canActivate: [AuthGuard] },
  { path: 'calendar', component: CalendarComponent, canActivate: [AuthGuard] },
  { path: 'settings', component: SettingsComponent, canActivate: [AuthGuard] }
];
