export interface EventLog {
  id: number;
  event_type: string;
  source: string;
  payload: unknown;
  created_at: string;
}
