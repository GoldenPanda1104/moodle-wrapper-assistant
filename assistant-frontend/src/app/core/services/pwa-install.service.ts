import { Injectable } from '@angular/core';

const DISMISS_STORAGE_KEY = 'pwa-install-dismissed';

export interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

/**
 * Servicio para el aviso "Instalar app" (PWA).
 * Captura beforeinstallprompt y permite mostrar un botón para instalar.
 */
@Injectable({ providedIn: 'root' })
export class PwaInstallService {
  private deferredPrompt: BeforeInstallPromptEvent | null = null;
  private _installAvailable = false;

  get installAvailable(): boolean {
    return this._installAvailable;
  }

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeinstallprompt', (e: Event) => {
        e.preventDefault();
        this.deferredPrompt = e as BeforeInstallPromptEvent;
        this._installAvailable = true;
      });
      window.addEventListener('appinstalled', () => {
        this.deferredPrompt = null;
        this._installAvailable = false;
        this.setDismissed(true);
      });
    }
  }

  /** True si el usuario ya instaló o cerró el aviso. */
  wasDismissed(): boolean {
    try {
      return localStorage.getItem(DISMISS_STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  }

  setDismissed(dismissed: boolean): void {
    try {
      if (dismissed) {
        localStorage.setItem(DISMISS_STORAGE_KEY, '1');
      } else {
        localStorage.removeItem(DISMISS_STORAGE_KEY);
      }
    } catch {}
  }

  /** True si estamos en modo standalone (app instalada o abierta como PWA). */
  get isStandalone(): boolean {
    if (typeof window === 'undefined') return false;
    return (
      window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true
    );
  }

  /** Muestra el diálogo nativo de instalación. Devuelve true si se mostró. */
  async install(): Promise<boolean> {
    if (!this.deferredPrompt) return false;
    await this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      this.deferredPrompt = null;
      this._installAvailable = false;
    }
    return outcome === 'accepted';
  }

  /** Si se debe mostrar el aviso de instalación (disponible, no descartado, no ya instalado). */
  shouldShowBanner(): boolean {
    return (
      this._installAvailable &&
      !this.wasDismissed() &&
      !this.isStandalone
    );
  }
}
