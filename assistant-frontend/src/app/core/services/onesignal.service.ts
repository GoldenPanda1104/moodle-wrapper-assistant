import { Injectable } from '@angular/core';

declare global {
  interface Window {
    OneSignal?: any;
  }
}

@Injectable({ providedIn: 'root' })
export class OneSignalService {
  private initialized = false;

  init(appId: string, webOrigin?: string): void {
    if (!appId || this.initialized) {
      return;
    }
    const OneSignal = (window.OneSignal = window.OneSignal || []);
    OneSignal.push(() => {
      OneSignal.init({
        appId,
        serviceWorkerPath: 'OneSignalSDKWorker.js',
        serviceWorkerUpdaterPath: 'OneSignalSDKUpdaterWorker.js',
        allowLocalhostAsSecureOrigin: window.location.hostname === 'localhost',
      });
      if (webOrigin) {
        OneSignal.setDefaultNotificationUrl(webOrigin);
      }
    });
    this.initialized = true;
  }

  login(externalUserId: string): void {
    const OneSignal = window.OneSignal;
    if (!OneSignal || !this.initialized) {
      return;
    }
    OneSignal.push(() => {
      OneSignal.login(externalUserId);
    });
  }

  logout(): void {
    const OneSignal = window.OneSignal;
    if (!OneSignal || !this.initialized) {
      return;
    }
    OneSignal.push(() => {
      OneSignal.logout();
    });
  }

  /** Devuelve true si el navegador soporta push. */
  isPushSupported(): boolean {
    const OneSignal = window.OneSignal;
    if (!OneSignal || !this.initialized) return false;
    try {
      return typeof OneSignal?.Notifications?.isPushSupported === 'function' && OneSignal.Notifications.isPushSupported();
    } catch {
      return false;
    }
  }

  /** Estado nativo del permiso: 'default' | 'granted' | 'denied'. */
  getPermissionNative(): 'default' | 'granted' | 'denied' {
    const OneSignal = window.OneSignal;
    if (!OneSignal?.Notifications) return 'denied';
    try {
      const p = OneSignal.Notifications.permissionNative;
      return p === 'granted' || p === 'denied' ? p : 'default';
    } catch {
      return 'denied';
    }
  }

  /** Solicita el permiso de notificaciones push (muestra el diálogo del navegador). */
  requestPermission(): Promise<boolean> {
    const OneSignal = window.OneSignal;
    if (!OneSignal || !this.initialized) {
      return Promise.resolve(false);
    }
    return new Promise((resolve) => {
      OneSignal.push(async () => {
        try {
          if (OneSignal.Notifications?.requestPermission) {
            const granted = await OneSignal.Notifications.requestPermission();
            resolve(!!granted);
          } else {
            resolve(false);
          }
        } catch {
          resolve(false);
        }
      });
    });
  }
}
