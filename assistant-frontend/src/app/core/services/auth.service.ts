import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface RegisterPayload {
  email: string;
  password: string;
}

interface LoginPayload {
  email: string;
  password: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private readonly http: HttpClient) {}
  private readonly baseUrl = '/api/v1/auth';
  private readonly accessKey = 'auth_access_token';
  private readonly refreshKey = 'auth_refresh_token';

  register(payload: RegisterPayload): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/register`, payload);
  }

  login(payload: LoginPayload): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.baseUrl}/login`, payload).pipe(
      tap((response) => this.storeTokens(response))
    );
  }

  refresh(): Observable<AuthResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    return this.http.post<AuthResponse>(`${this.baseUrl}/refresh`, {
      refresh_token: refreshToken
    }).pipe(tap((response) => this.storeTokens(response)));
  }

  logout(): Observable<unknown> {
    const refreshToken = this.getRefreshToken();
    this.clearTokens();
    if (!refreshToken) {
      return this.http.post(`${this.baseUrl}/logout`, { refresh_token: '' });
    }
    return this.http.post(`${this.baseUrl}/logout`, { refresh_token: refreshToken });
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.accessKey);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshKey);
  }

  isAuthenticated(): boolean {
    return Boolean(this.getAccessToken());
  }

  clearSession(): void {
    this.clearTokens();
  }

  private storeTokens(response: AuthResponse): void {
    localStorage.setItem(this.accessKey, response.access_token);
    localStorage.setItem(this.refreshKey, response.refresh_token);
  }

  private clearTokens(): void {
    localStorage.removeItem(this.accessKey);
    localStorage.removeItem(this.refreshKey);
  }
}
