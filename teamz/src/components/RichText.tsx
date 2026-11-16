import { Fragment, type ReactNode } from 'react';

/**
 * Tiny, dependency-free markdown-ish renderer.
 * Supports fenced code blocks, HTML presentation blocks, **bold**, *italic*,
 * `inline code`, bullet lists and > blockquotes.
 * Builds React nodes — never uses dangerouslySetInnerHTML for normal text.
 */

const INLINE = /(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|_[^_\n]+_)/g;

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(INLINE).filter((p) => p !== '');
  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return (
        <code className="inline-code" key={key}>
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={key}>{part.slice(2, -2)}</strong>;
    }
    if (
      (part.startsWith('*') && part.endsWith('*') && part.length > 2) ||
      (part.startsWith('_') && part.endsWith('_') && part.length > 2)
    ) {
      return <em key={key}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={key}>{part}</Fragment>;
  });
}

function isPresentationLang(lang: string): boolean {
  const l = (lang || '').trim().toLowerCase();
  return l === 'presentation' || l === 'html:presentation' || l === 'slides' || l === 'slide' || l === 'presentation-html';
}

function PresentationBlock({ html }: { html: string }) {
  const src = (html || '').trim();
  return (
    <div className="presentation-block">
      <div className="presentation-head">
        <span className="presentation-badge">HTML presentation</span>
      </div>
      <iframe
        className="presentation-frame"
        sandbox="allow-scripts allow-forms allow-popups allow-modals"
        srcDoc={src}
        title="HTML presentation"
        loading="lazy"
      />
    </div>
  );
}

function renderTextBlocks(text: string, keyBase: string): ReactNode[] {
  const blocks = text.split(/```/);
  const out: ReactNode[] = [];

  blocks.forEach((block, blockIndex) => {
    // Odd indices are fenced blocks.
    if (blockIndex % 2 === 1) {
      const firstNewline = block.indexOf('\n');
      const lang = firstNewline > -1 ? block.slice(0, firstNewline).trim() : '';
      const code = (firstNewline > -1 ? block.slice(firstNewline + 1) : block).replace(/\n$/, '');
      if (isPresentationLang(lang)) {
        out.push(<PresentationBlock key={`${keyBase}-pres-${blockIndex}`} html={code} />);
      } else {
        out.push(
          <pre className="code-block" key={`${keyBase}-code-${blockIndex}`}>
            {lang && <span className="code-lang">{lang}</span>}
            <code>{code}</code>
          </pre>,
        );
      }
      return;
    }

    const lines = block.split('\n').filter((l, i, arr) => !(l.trim() === '' && (i === 0 || i === arr.length - 1)));
    if (lines.length === 0) return;

    const nodes: ReactNode[] = [];
    let listBuffer: string[] = [];

    const flushList = () => {
      if (listBuffer.length === 0) return;
      nodes.push(
        <ul className="md-list" key={`${keyBase}-ul-${blockIndex}-${nodes.length}`}>
          {listBuffer.map((item, i) => (
            <li key={item || i}>{renderInline(item, `${keyBase}-li-${blockIndex}-${nodes.length}-${i}`)}</li>
          ))}
        </ul>,
      );
      listBuffer = [];
    };

    lines.forEach((line, i) => {
      const trimmed = line.trim();
      const bullet = trimmed.match(/^[•\-*]\s+(.*)$/);
      if (bullet) {
        listBuffer.push(bullet[1]);
        return;
      }
      flushList();

      if (trimmed.startsWith('>')) {
        nodes.push(
          <blockquote className="md-quote" key={`${keyBase}-q-${blockIndex}-${i}`}>
            {renderInline(trimmed.replace(/^>\s?/, ''), `${keyBase}-q-${blockIndex}-${i}`)}
          </blockquote>,
        );
        return;
      }
      if (trimmed === '') {
        nodes.push(<div className="md-gap" key={`${keyBase}-gap-${blockIndex}-${i}`} />);
        return;
      }
      nodes.push(
        <p className="md-p" key={`${keyBase}-p-${blockIndex}-${i}`}>
          {renderInline(trimmed, `${keyBase}-p-${blockIndex}-${i}`)}
        </p>,
      );
    });
    flushList();

    out.push(<Fragment key={`${keyBase}-block-${blockIndex}`}>{nodes}</Fragment>);
  });

  return out;
}

function splitPresentationMarkers(text: string): Array<{ type: 'text' | 'presentation'; content: string }> {
  const parts: Array<{ type: 'text' | 'presentation'; content: string }> = [];
  const re = /:::presentation\s*\n([\s\S]*?)\n:::/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ type: 'text', content: text.slice(last, m.index) });
    parts.push({ type: 'presentation', content: m[1] });
    last = re.lastIndex;
  }
  if (last < text.length) parts.push({ type: 'text', content: text.slice(last) });
  return parts.length ? parts : [{ type: 'text', content: text }];
}

export function RichText({ text }: { text: string }) {
  const segments = splitPresentationMarkers(text || '');
  return (
    <div className="rich-text">
      {segments.map((seg, i) => {
        if (seg.type === 'presentation') return <PresentationBlock key={`seg-pres-${i}`} html={seg.content} />;
        return <Fragment key={`seg-text-${i}`}>{renderTextBlocks(seg.content, `s${i}`)}</Fragment>;
      })}
    </div>
  );
}
