export type Theme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'weathergpt-theme';

export function getInitialTheme(): Theme {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') {
      return saved;
    }
  } catch {
    // localStorage might be blocked in strict sandboxes
  }
  return 'dark'; // Default theme is dark as specified
}

export function applyTheme(theme: Theme): void {
  try {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Ignore storage errors
  }
}
