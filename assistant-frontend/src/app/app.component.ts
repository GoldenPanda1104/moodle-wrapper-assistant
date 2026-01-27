import { Component, DestroyRef, Inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NgIf } from '@angular/common';
import { AuthService } from './core/services/auth.service';
import { NotificationService } from './core/services/notification.service';
import { UserService } from './core/services/user.service';
import { OneSignalService } from './core/services/onesignal.service';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { of, switchMap, timer } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgIf],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'assistant-frontend';
  unreadCount = 0;
  private notificationsInitialized = false;

  constructor(
    private readonly auth: AuthService,
    @Inject(NotificationService) private readonly notifications: NotificationService,
    private readonly users: UserService,
    private readonly oneSignal: OneSignalService,
    private readonly destroyRef: DestroyRef,
  ) {
    this.watchAuthentication();
  }

  isAuthenticated(): boolean {
    return this.auth.isAuthenticated();
  }

  private watchAuthentication(): void {
    timer(0, 2000)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        if (this.isAuthenticated()) {
          this.bootstrapNotifications();
        }
      });
  }

  private bootstrapNotifications(): void {
    if (!this.isAuthenticated() || this.notificationsInitialized) {
      return;
    }
    this.notificationsInitialized = true;

    this.notifications
      .getConfig()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((config) => {
        if (config.onesignal_app_id) {
          this.oneSignal.init(config.onesignal_app_id, config.onesignal_web_origin);
          this.users
            .getProfile()
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe((profile) => {
              this.oneSignal.login(String(profile.id));
            });
        }
      });

    timer(0, 60000)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        switchMap(() =>
          this.isAuthenticated() ? this.notifications.getUnreadCount() : of({ count: 0 })
        ),
      )
      .subscribe((data) => {
        this.unreadCount = data.count;
      });
  }
}
