import { MoodleCourse } from './moodle-course.model';

export interface MoodleGradeItem {
  id: number;
  course_id: number;
  external_id: string;
  item_type: string;
  title: string;
  grade_value: number | null;
  grade_display: string | null;
  url: string | null;
  available_at: string | null;
  due_at: string | null;
  submission_status: string | null;
  grading_status: string | null;
  last_submission_at: string | null;
  attempts_allowed: number | null;
  time_limit_minutes: number | null;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
  course: MoodleCourse;
}
