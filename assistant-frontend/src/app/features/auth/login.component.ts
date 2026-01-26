import { Component } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, NgIf],
  templateUrl: './login.component.html'
})
export class LoginComponent {
  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

  errorMessage = '';
  loading = false;

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

  submit(): void {
    if (this.form.invalid || this.loading) {
      return;
    }
    this.loading = true;
    this.errorMessage = '';
    const payload = this.form.getRawValue();
    this.auth.login(payload as { email: string; password: string }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/']);
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'No pudimos iniciar sesion. Revisa tus credenciales.';
      }
    });
  }
}
