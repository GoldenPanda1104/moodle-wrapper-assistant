export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  body: string;
  notification_type: string;
  source: string;
  payload?: Record<string, unknown> | null;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationPreferences {
  in_app_enabled: boolean;
  email_enabled: boolean;
  push_enabled: boolean;
  daily_digest_enabled: boolean;
  timezone?: string | null;
  digest_hour: number;
}

export interface NotificationConfig {
  onesignal_app_id: string;
  onesignal_web_origin: string;
  onesignal_enabled: boolean;
}
