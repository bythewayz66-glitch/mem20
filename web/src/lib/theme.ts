/* Theme: dark by default, light on request, persisted per browser.
 *
 * The tokens live in styles/surfaces.css under `:root` (dark, inherited from
 * styles.css) and `:root[data-theme="light"]` (light). This module only decides
 * which one is active and remembers the choice. It never writes colours itself
 * \u2014 a second place that knows the palette is a second palette.
 *
 * The initial value is applied by an inline script in index.html BEFORE first
 * paint, so a light-theme user does not get a dark flash. This module reads the
 * same key and keeps the two in step.
 */

export type Theme = 'dark' | 'light';

export const THEME_KEY = 'mem20.theme';

export function isTheme(v: unknown): v is Theme {
  return v === 'dark' || v === 'light';
}

/** The stored theme, or the OS preference when nothing is stored. */
export function getTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (isTheme(stored)) return stored;
  } catch {
    /* private mode / storage disabled \u2014 fall through to the OS preference */
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  return 'dark';
}

/** Write the theme onto <html> so the CSS token block switches. */
export function applyTheme(theme: Theme): void {
  if (typeof document === 'undefined') return;
  document.documentElement.setAttribute('data-theme', theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', theme === 'light' ? '#f6f7fb' : '#0a0e1a');
}

export function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* storage disabled: the theme still applies for this session */
  }
  applyTheme(theme);
}

/** Apply the resolved theme and return it, for the caller's initial state. */
export function initTheme(): Theme {
  const theme = getTheme();
  applyTheme(theme);
  return theme;
}
