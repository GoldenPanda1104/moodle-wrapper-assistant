export interface Task {
  id: number;
  title: string;
  source: string;
  category: string;
  status: 'pending' | 'ready' | 'blocked' | 'done';
  priority: 'low' | 'medium' | 'high' | 'critical';
  deadline?: string;
  action_url?: string;
  action_label?: string;
}
