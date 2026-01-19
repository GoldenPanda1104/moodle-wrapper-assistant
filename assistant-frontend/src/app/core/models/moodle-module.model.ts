export interface MoodleModule {
  id: number;
  course_id: number;
  external_id: string;
  title: string;
  visible: boolean;
  blocked: boolean;
  block_reason?: string | null;
  has_survey: boolean;
  url?: string | null;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
  course: {
    id: number;
    external_id: string;
    name: string;
    last_seen_at: string;
    created_at: string;
    updated_at: string;
  };
}
