import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export type AppTheme = 'dark' | 'light';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private static readonly THEME_STORAGE_KEY = 'watchme-theme';
  private currentThemeSubject = new BehaviorSubject<AppTheme>('dark');

  public currentTheme$: Observable<AppTheme> = this.currentThemeSubject.asObservable();
  public isDarkMode$: Observable<boolean> = this.currentTheme$.pipe(
    map(theme => theme === 'dark')
  );

  constructor() {
    this.initializeTheme();
  }

  get currentTheme(): AppTheme {
    return this.currentThemeSubject.value;
  }

  get isDarkMode(): boolean {
    return this.currentThemeSubject.value === 'dark';
  }

  /**
   * Returns the corresponding placeholder SVG path based on active theme
   */
  get placeholderUrl(): string {
    return this.isDarkMode ? 'assets/placeholder-dark.svg' : 'assets/placeholder-light.svg';
  }

  /**
   * Initializes theme on app startup based on stored preference or system setting
   */
  public initializeTheme(): void {
    const savedTheme = localStorage.getItem(ThemeService.THEME_STORAGE_KEY) as AppTheme | null;
    if (savedTheme === 'dark' || savedTheme === 'light') {
      this.applyTheme(savedTheme);
    } else {
      // Default according to system preference
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.applyTheme(prefersDark ? 'dark' : 'light');
    }

    // React to system preference changes if the user hasn't pinned an explicit choice
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const hasExplicitChoice = localStorage.getItem(ThemeService.THEME_STORAGE_KEY);
        if (!hasExplicitChoice) {
          this.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  }

  /**
   * Toggles between dark and light modes
   */
  public toggleTheme(): void {
    const nextTheme: AppTheme = this.isDarkMode ? 'light' : 'dark';
    this.setTheme(nextTheme);
  }

  /**
   * Sets and persists the specified theme
   */
  public setTheme(theme: AppTheme): void {
    localStorage.setItem(ThemeService.THEME_STORAGE_KEY, theme);
    this.applyTheme(theme);
  }

  private applyTheme(theme: AppTheme): void {
    this.currentThemeSubject.next(theme);
    const root = document.documentElement;

    if (theme === 'dark') {
      root.classList.add('ion-palette-dark');
      root.setAttribute('data-bs-theme', 'dark');
      root.style.colorScheme = 'dark';
      const meta = document.querySelector('meta[name="color-scheme"]');
      if (meta) {
        meta.setAttribute('content', 'dark');
      }
    } else {
      root.classList.remove('ion-palette-dark');
      root.setAttribute('data-bs-theme', 'light');
      root.style.colorScheme = 'light';
      const meta = document.querySelector('meta[name="color-scheme"]');
      if (meta) {
        meta.setAttribute('content', 'light');
      }
    }
  }
}
