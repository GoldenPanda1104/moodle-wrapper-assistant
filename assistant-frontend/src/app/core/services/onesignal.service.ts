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
    OneSignal.login(externalUserId);
  }

  logout(): void {
    const OneSignal = window.OneSignal;
    if (!OneSignal || !this.initialized) {
      return;
    }
    OneSignal.logout();
  }
}
