import { Routes } from '@angular/router';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { TasksComponent } from './features/tasks/tasks.component';
import { EventsComponent } from './features/events/events.component';
import { CoursesComponent } from './features/courses/courses.component';
import { ModulesComponent } from './features/modules/modules.component';
import { SurveysComponent } from './features/surveys/surveys.component';
import { GradesComponent } from './features/grades/grades.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'tasks', component: TasksComponent },
  { path: 'events', component: EventsComponent },
  { path: 'courses', component: CoursesComponent },
  { path: 'modules', component: ModulesComponent },
  { path: 'surveys', component: SurveysComponent },
  { path: 'grades', component: GradesComponent }
];
