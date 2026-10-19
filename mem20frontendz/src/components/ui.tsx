/**
 * Shared primitives for the mem20 shell.
 *
 * Every route renders loading / empty / error through these, so those three
 * states can never be forgotten on a new surface and never look different from
 * one another.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import type { Loaded } from '../api/types';

/* ------------------------------------------------------------------- icons */

type IconProps = { size?: number; className?: string };

const svg = (path: ReactNode, viewBox = '0 0 24 24') =>
  function Icon({ size = 16, className }: IconProps) {
    return (
      <svg
        width={size}
        height={size}
        viewBox={viewBox}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        aria-hidden="true"
        focusable="false"
      >
        {path}
      </svg>
    );
  };

export const IconBoard = svg(
  <>
    <rect x="3" y="4" width="5" height="16" rx="1.5" />
    <rect x="10" y="4" width="5" height="10" rx="1.5" />
    <rect x="17" y="4" width="4" height="13" rx="1.5" />
  </>,
);

export const IconDream = svg(
  <>
    <path d="M12 3a9 9 0 1 0 9 9c0-.5-.04-1-.12-1.48A7 7 0 0 1 12 3Z" />
    <path d="M8 14h.01M7 9h.01" />
  </>,
);

export const IconCube = svg(
  <>
    <path d="M12 2.8 20 7v10l-8 4.2L4 17V7l8-4.2Z" />
    <path d="M4 7l8 4.2L20 7M12 11.2V21" />
  </>,
);

export const IconUsers = svg(
  <>
    <circle cx="9" cy="8" r="3.2" />
    <path d="M2.8 20a6.2 6.2 0 0 1 12.4 0" />
    <path d="M16.5 5.4a3.2 3.2 0 0 1 0 6M17.5 14.2A6.2 6.2 0 0 1 21.2 20" />
  </>,
);

export const IconBook = svg(
  <>
    <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5A2.5 2.5 0 0 0 4 22V4.5Z" />
    <path d="M4 17.5A2.5 2.5 0 0 1 6.5 15H20" />
  </>,
);

export const IconLink = svg(
  <>
    <path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1" />
    <path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1" />
  </>,
);

export const IconSearch = svg(
  <>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="m20 20-4.6-4.6" />
  </>,
);

export const IconPlus = svg(<path d="M12 5v14M5 12h14" />);
export const IconX = svg(<path d="M6 6l12 12M18 6 6 18" />);
export const IconCheck = svg(<path d="m4 12.5 5 5L20 6.5" />);
export const IconWarn = svg(
  <>
    <path d="M12 3.5 2.8 20h18.4L12 3.5Z" />
    <path d="M12 9.5v4.5M12 17h.01" />
  </>,
);
export const IconInfo = svg(
  <>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5M12 7.6h.01" />
  </>,
);
export const IconRefresh = svg(
  <>
    <path d="M20 11a8 8 0 1 0-2.3 6.1" />
    <path d="M20 4v7h-7" />
  </>,
);
export const IconMenu = svg(<path d="M4 7h16M4 12h16M4 17h16" />);
export const IconSun = svg(
  <>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
  </>,
);
export const IconMoon = svg(<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />);
export const IconTrash = svg(
  <>
    <path d="M4 7h16M9.5 7V4.8h5V7M6.5 7l1 13h9l1-13" />
  </>,
);
export const IconArrowRight = svg(<path d="M5 12h13M13 6.5 18.5 12 13 17.5" />);
export const IconPlay = svg(<path d="M7 4.5v15l13-7.5-13-7.5Z" />);
export const IconShield = svg(
  <>
    <path d="M12 2.8 20 6v6.2c0 4.4-3.2 7.6-8 9-4.8-1.4-8-4.6-8-9V6l8-3.2Z" />
    <path d="m8.5 12 2.6 2.6 4.6-4.8" />
  </>,
);
export const IconRoute = svg(
  <>
    <circle cx="5.5" cy="5.5" r="2.5" />
    <circle cx="18.5" cy="18.5" r="2.5" />
    <path d="M8 5.5h6.5A3.5 3.5 0 0 1 18 9v2.5M16 18.5H9.5A3.5 3.5 0 0 1 6 15v-2.5" />
  </>,
);

/* -------------------------------------------------------------- provenance */

/**
 * The provenance badge.
 *
 * `live` and `snapshot` are deliberately different colours *and* different
 * words: this is the mechanism that keeps a capture from reading as a live
 * read. It is rendered in every route header. If a surface ever has no `at`
 * value, that is a bug — the badge says so rather than looking normal.
 */
export function Provenance({ loaded, what }: { loaded: Loaded<unknown>; what: string }) {
  const isLive = loaded.source === 'live';
  const stamp = loaded.at ? new Date(loaded.at) : null;
  const time =
    stamp && !Number.isNaN(stamp.getTime())
      ? stamp.toLocaleString(undefined, {
          year: 'numeric',
          month: 'short',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
        })
      : 'unknown time';

  return (
    <span
      className="provenance"
      data-source={loaded.source}
      title={loaded.note ?? `${what} read from the live backend.`}
    >
      <span className="provenance-dot" aria-hidden="true" />
      {isLive ? 'Live' : 'Capture'}
      <span aria-hidden="true" style={{ opacity: 0.5 }}>
        ·
      </span>
      <span className="mono" style={{ fontSize: 10.5 }}>
        {time}
      </span>
      {isLive && loaded.latencyMs !== undefined ? (
        <>
          <span aria-hidden="true" style={{ opacity: 0.5 }}>
            ·
          </span>
          <span className="mono" style={{ fontSize: 10.5 }}>
            {loaded.latencyMs}ms
          </span>
        </>
      ) : null}
    </span>
  );
}

/** The explanatory sentence under the header when a surface is on a capture. */
export function CaptureNotice({ loaded }: { loaded: Loaded<unknown> }) {
  if (loaded.source !== 'snapshot' || !loaded.note) return null;
  return (
    <div className="notice" data-tone="warn" style={{ marginBottom: 14 }}>
      <IconWarn className="notice-icon" size={16} />
      <div>
        <strong>Showing a capture, not a live read.</strong> {loaded.note}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ states */

export function LoadingState({ rows = 3, label = 'Loading' }: { rows?: number; label?: string }) {
  return (
    <div aria-busy="true" aria-live="polite" style={{ display: 'grid', gap: 10 }}>
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ height: i === 0 ? 54 : 44, opacity: 1 - i * 0.12 }}
        />
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  children,
  icon,
  action,
}: {
  title: string;
  children?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="state">
      <div className="state-inner">
        <div className="state-icon">{icon ?? <IconInfo size={20} />}</div>
        <h3>{title}</h3>
        {children ? <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>{children}</div> : null}
        {action ? <div style={{ marginTop: 6 }}>{action}</div> : null}
      </div>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="state" role="alert">
      <div className="state-inner">
        <div className="state-icon" style={{ color: 'var(--red)' }}>
          <IconWarn size={20} />
        </div>
        <h3>That read failed</h3>
        <p className="mono" style={{ fontSize: 12 }}>
          {error.message}
        </p>
        {onRetry ? (
          <button type="button" className="btn btn-sm" onClick={onRetry} style={{ marginTop: 8 }}>
            <IconRefresh size={13} /> Retry
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function Notice({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'warn' | 'error' | 'ok';
  children: ReactNode;
}) {
  const Icon = tone === 'warn' || tone === 'error' ? IconWarn : IconInfo;
  return (
    <div className="notice" data-tone={tone}>
      <Icon className="notice-icon" size={16} />
      <div>{children}</div>
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {hint ? <div className="stat-hint">{hint}</div> : null}
    </div>
  );
}

/* ------------------------------------------------------------------- modal */

export function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    lastFocus.current = document.activeElement as HTMLElement | null;

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key !== 'Tab' || !panelRef.current) return;
      // Focus trap: keep Tab inside the dialog.
      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKey);
    const timer = window.setTimeout(() => {
      panelRef.current?.querySelector<HTMLElement>('input, select, textarea, button')?.focus();
    }, 30);

    return () => {
      document.removeEventListener('keydown', onKey);
      window.clearTimeout(timer);
      lastFocus.current?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="modal-scrim"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} ref={panelRef}>
        <div className="spread" style={{ alignItems: 'flex-start' }}>
          <div>
            <h2>{title}</h2>
            {subtitle ? <p className="modal-sub">{subtitle}</p> : null}
          </div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close">
            <IconX size={15} />
          </button>
        </div>
        <div style={{ marginTop: subtitle ? 0 : 14 }}>{children}</div>
        {footer ? <div className="modal-actions">{footer}</div> : null}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------- misc */

export function Chip({
  children,
  tone,
  title,
}: {
  children: ReactNode;
  tone?: 'accent' | 'green' | 'amber' | 'red' | 'dream';
  title?: string;
}) {
  return (
    <span className={`chip${tone ? ` chip-${tone}` : ''}`} title={title}>
      {children}
    </span>
  );
}

export function plural(n: number, one: string, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

export function relTime(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const ms = typeof value === 'number' ? value * 1000 : Date.parse(value);
  if (Number.isNaN(ms)) return '—';
  const secs = Math.round((Date.now() - ms) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
  return `${Math.round(secs / 86400)}d ago`;
}

export function shortDate(value: string | null | undefined): string {
  if (!value) return '—';
  const ms = Date.parse(value);
  if (Number.isNaN(ms)) return value;
  return new Date(ms).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
}
