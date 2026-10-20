/* Small shared UI primitives. Nothing here invents data — these only render. */
import React from 'react';

export function Pill({
  tone = '',
  children,
  dot = false,
  mono = false,
}: {
  tone?: '' | 'green' | 'amber' | 'red' | 'cyan' | 'violet';
  children: React.ReactNode;
  dot?: boolean;
  mono?: boolean;
}) {
  return (
    <span className={`pill ${tone} ${mono ? 'mono-pill' : ''}`}>
      {dot && <span className="dot" />}
      {children}
    </span>
  );
}

export function Panel({
  title,
  right,
  children,
  bodyStyle,
}: {
  title: React.ReactNode;
  right?: React.ReactNode;
  children: React.ReactNode;
  bodyStyle?: React.CSSProperties;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h3>{title}</h3>
        <span className="spacer" />
        {right}
      </div>
      <div className="panel-body" style={bodyStyle}>
        {children}
      </div>
    </section>
  );
}

export function Notice({
  tone = '',
  title,
  children,
}: {
  tone?: '' | 'ok' | 'warn' | 'bad';
  title: React.ReactNode;
  children?: React.ReactNode;
}) {
  const mark = tone === 'ok' ? '✓' : tone === 'bad' ? '✕' : tone === 'warn' ? '!' : 'i';
  return (
    <div className={`notice ${tone}`}>
      <span className="nico mono">{mark}</span>
      <div>
        <div>{title}</div>
        {children && <div className="nb">{children}</div>}
      </div>
    </div>
  );
}

export function Stat({ k, v, sub }: { k: string; v: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="stat">
      <div className="k">{k}</div>
      <div className="v">
        {v} {sub && <small>{sub}</small>}
      </div>
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Mono({ children }: { children: React.ReactNode }) {
  return <span className="mono">{children}</span>
}
