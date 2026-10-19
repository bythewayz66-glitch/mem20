/**
 * Hash-based router.
 *
 * Deliberately not react-router: the app is served from a project sub-path
 * (`/mem20frontendz/`) on GitHub Pages, where a history-API router needs a 404
 * fallback shim to survive a refresh on a deep link. A hash router needs none,
 * so it works on Pages, on a bare `vite preview`, and behind any reverse proxy
 * without configuration.
 */

import { useEffect, useState } from 'react';

export type RouteId = 'kanban' | 'dreams' | 'agents' | 'teamz' | 'tools' | 'docs' | 'status';

export interface Route {
  id: RouteId;
  /** Optional second segment, e.g. `dreams/<dream_id>` or `kanban/<board>`. */
  param: string;
}

const ROUTES: RouteId[] = ['kanban', 'dreams', 'agents', 'teamz', 'tools', 'docs', 'status'];

function parse(hash: string): Route {
  const clean = hash.replace(/^#\/?/, '').trim();
  if (!clean) return { id: 'kanban', param: '' };
  const [head, ...rest] = clean.split('/');
  const id = (ROUTES as string[]).includes(head) ? (head as RouteId) : 'kanban';
  return { id, param: rest.join('/') };
}

export function useRoute(): [Route, (id: RouteId, param?: string) => void] {
  const [route, setRoute] = useState<Route>(() => parse(window.location.hash));

  useEffect(() => {
    const onChange = () => setRoute(parse(window.location.hash));
    window.addEventListener('hashchange', onChange);
    // Normalise a bare URL to an explicit route so the nav highlight is right.
    if (!window.location.hash) window.location.replace('#/kanban');
    return () => window.removeEventListener('hashchange', onChange);
  }, []);

  const navigate = (id: RouteId, param = '') => {
    const next = `#/${id}${param ? `/${param}` : ''}`;
    if (window.location.hash === next) return;
    window.location.hash = next;
  };

  return [route, navigate];
}

/** Scroll the main region to the top on every route change. */
export function useScrollReset(key: string) {
  useEffect(() => {
    document.querySelector('.content')?.scrollTo({ top: 0 });
  }, [key]);
}
