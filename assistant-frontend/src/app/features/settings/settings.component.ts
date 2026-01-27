import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { MoodleVaultService, VaultStatus } from '../../core/services/moodle-vault.service';
import { Router } from '@angular/router';
import { NgIf } from '@angular/common';
import { NotificationService } from '../../core/services/notification.service';
import { NotificationPreferences } from '../../core/models/notification.model';
import { OneSignalService } from '../../core/services/onesignal.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [ReactiveFormsModule, NgIf],
  templateUrl: './settings.component.html'
})
export class SettingsComponent implements OnInit {
  constructor(
    private readonly fb: FormBuilder,
    private readonly vault: MoodleVaultService,
    private readonly auth: AuthService,
    private readonly notifications: NotificationService,
    private readonly oneSignal: OneSignalService,
    private readonly router: Router,
  ) {}

  status: VaultStatus | null = null;
  message = '';
  errorMessage = '';
  loading = false;
  cronLoading = false;
  prefsLoading = false;

  form = this.fb.group({
    moodle_username: ['', Validators.required],
    moodle_password: ['', Validators.required],
    app_password: ['', Validators.required]
  });

  cronForm = this.fb.group({
    app_password: ['', Validators.required]
  });

  notificationForm = this.fb.group({
    in_app_enabled: [true],
    email_enabled: [true],
    push_enabled: [true],
    daily_digest_enabled: [true],
    digest_hour: [8, Validators.required],
    timezone: ['']
  });

  ngOnInit(): void {
    this.refreshStatus();
    this.loadPreferences();
  }

  refreshStatus(): void {
    this.vault.getStatus().subscribe({
      next: (status) => {
        this.status = status;
      }
    });
  }

  saveCredentials(): void {
    if (this.form.invalid || this.loading) {
      return;
    }
    this.loading = true;
    this.message = '';
    this.errorMessage = '';
    const raw = this.form.getRawValue();
    const payload = {
      moodle_username: raw.moodle_username ?? '',
      moodle_password: raw.moodle_password ?? '',
      app_password: raw.app_password ?? ''
    };
    this.vault.storeCredentials(payload).subscribe({
      next: (status) => {
        this.loading = false;
        this.status = status;
        this.message = 'Credenciales guardadas y cron habilitado.';
        this.form.reset();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No pudimos guardar las credenciales.';
      }
    });
  }

  toggleCron(enable: boolean): void {
    if (this.cronForm.invalid || this.cronLoading) {
      return;
    }
    this.cronLoading = true;
    this.message = '';
    this.errorMessage = '';
    const appPassword = this.cronForm.getRawValue().app_password || '';
    const request = enable ? this.vault.enableCron(appPassword) : this.vault.disableCron();
    request.subscribe({
      next: (status) => {
        this.cronLoading = false;
        this.status = status;
        this.message = enable ? 'Cron habilitado.' : 'Cron deshabilitado.';
        this.cronForm.reset();
      },
      error: () => {
        this.cronLoading = false;
        this.errorMessage = 'No pudimos actualizar el cron.';
      }
    });
  }

  loadPreferences(): void {
    this.prefsLoading = true;
    this.notifications.getPreferences().subscribe({
      next: (prefs) => {
        this.prefsLoading = false;
        this.notificationForm.patchValue(prefs);
      },
      error: () => {
        this.prefsLoading = false;
      }
    });
  }

  savePreferences(): void {
    if (this.notificationForm.invalid || this.prefsLoading) {
      return;
    }
    this.prefsLoading = true;
    this.message = '';
    this.errorMessage = '';
    const raw = this.notificationForm.getRawValue();
    const digestHour = Number(raw.digest_hour);
    const payload: NotificationPreferences = {
      in_app_enabled: Boolean(raw.in_app_enabled),
      email_enabled: Boolean(raw.email_enabled),
      push_enabled: Boolean(raw.push_enabled),
      daily_digest_enabled: Boolean(raw.daily_digest_enabled),
      digest_hour: Number.isFinite(digestHour) ? digestHour : 8,
      timezone: raw.timezone ? String(raw.timezone) : null,
    };
    this.notifications.updatePreferences(payload).subscribe({
      next: () => {
        this.prefsLoading = false;
        this.message = 'Preferencias de notificacion actualizadas.';
      },
      error: () => {
        this.prefsLoading = false;
        this.errorMessage = 'No pudimos guardar las preferencias.';
      }
    });
  }

  logout(): void {
    this.auth.logout().subscribe({
      next: () => {
        this.oneSignal.logout();
        this.router.navigate(['/login']);
      },
      error: () => {
        this.oneSignal.logout();
        this.router.navigate(['/login']);
      }
    });
  }
}
