import { Component, DestroyRef, Inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NgIf } from '@angular/common';
import { AuthService } from './core/services/auth.service';
import { NotificationService } from './core/services/notification.service';
import { UserService } from './core/services/user.service';
import { OneSignalService } from './core/services/onesignal.service';
import { PwaInstallService } from './core/services/pwa-install.service';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { of, switchMap, timer } from 'rxjs';

const PUSH_BANNER_DISMISSED_KEY = 'suantechs-study-push-banner-dismissed';
const PUSH_AUTO_PROMPTED_KEY = 'suantechs-study-push-auto-prompted';

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
  /** Hay OneSignal configurado y ya inicializado. */
  hasPushAvailable = false;
  /** El usuario cerró el aviso de activar push sin aceptar. */
  pushBannerDismissed = false;
  /** Permiso de notificaciones ya concedido. */
  pushPermissionGranted = false;
  /** Menú móvil abierto. */
  mobileMenuOpen = false;

  constructor(
    private readonly auth: AuthService,
    @Inject(NotificationService) private readonly notifications: NotificationService,
    private readonly users: UserService,
    private readonly oneSignal: OneSignalService,
    public readonly pwaInstall: PwaInstallService,
    private readonly destroyRef: DestroyRef,
    private readonly router: Router,
  ) {
    this.watchAuthentication();
    this.router.events.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.closeMobileMenu());
  }

  async installPwa(): Promise<void> {
    await this.pwaInstall.install();
  }

  dismissPwaBanner(): void {
    this.pwaInstall.setDismissed(true);
  }

  dismissPushBanner(): void {
    this.pushBannerDismissed = true;
    try {
      localStorage.setItem(PUSH_BANNER_DISMISSED_KEY, '1');
    } catch {}
  }

  async requestPushPermission(): Promise<void> {
    const granted = await this.oneSignal.requestPermission();
    if (granted) {
      this.pushPermissionGranted = true;
      this.pushBannerDismissed = true;
    }
  }

  toggleMobileMenu(): void {
    this.mobileMenuOpen = !this.mobileMenuOpen;
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen = false;
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

    try {
      this.pushBannerDismissed = localStorage.getItem(PUSH_BANNER_DISMISSED_KEY) === '1';
    } catch {}

    this.notifications
      .getConfig()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((config) => {
        if (config.onesignal_app_id) {
          this.oneSignal.init(config.onesignal_app_id, config.onesignal_web_origin);
          this.hasPushAvailable = true;
          this.users
            .getProfile()
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe((profile) => {
              this.oneSignal.login(String(profile.id));
              // Solicitar permiso de push una vez por sesión tras un breve delay.
              try {
                const alreadyPrompted = sessionStorage.getItem(PUSH_AUTO_PROMPTED_KEY) === '1';
                if (!alreadyPrompted) {
                  sessionStorage.setItem(PUSH_AUTO_PROMPTED_KEY, '1');
                  setTimeout(() => this.requestPushPermission(), 1500);
                }
              } catch {}
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
