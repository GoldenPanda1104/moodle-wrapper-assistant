import { MoodleCourse } from './moodle-course.model';
import { MoodleModule } from './moodle-module.model';

export interface MoodleSurvey {
  id: number;
  module_id: number;
  course_id: number;
  external_id: string;
  title: string;
  url?: string | null;
  completion_url?: string | null;
  last_seen_at: string;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  course?: MoodleCourse;
  module?: MoodleModule;
}
