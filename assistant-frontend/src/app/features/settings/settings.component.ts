import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { MoodleVaultService, VaultStatus } from '../../core/services/moodle-vault.service';
import { Router } from '@angular/router';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [ReactiveFormsModule, NgIf],
  templateUrl: './settings.component.html'
})
export class SettingsComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly vault = inject(MoodleVaultService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  status: VaultStatus | null = null;
  message = '';
  errorMessage = '';
  loading = false;
  cronLoading = false;

  form = this.fb.group({
    moodle_username: ['', Validators.required],
    moodle_password: ['', Validators.required],
    app_password: ['', Validators.required]
  });

  cronForm = this.fb.group({
    app_password: ['', Validators.required]
  });

  ngOnInit(): void {
    this.refreshStatus();
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

  logout(): void {
    this.auth.logout().subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: () => {
        this.router.navigate(['/login']);
      }
    });
  }
}
