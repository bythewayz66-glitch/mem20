/**
 * Two small hooks used by every route.
 *
 * `useAsync` exists so no view ever hand-rolls loading/error/empty handling —
 * the same three states, rendered the same way, on every surface.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  /** Force a re-fetch (used by the "Retry" action). */
  reload: () => void;
}

export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [nonce, setNonce] = useState(0);

  // The loader is recreated on every render; holding it in a ref keeps the
  // effect keyed on the caller's deps alone.
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);

    loaderRef
      .current()
      .then((value) => {
        if (alive) {
          setData(value);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (alive) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setLoading(false);
        }
      });

    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { data, loading, error, reload };
}

/** Persisted string state (theme, last board) with a safe fallback. */
export function usePersisted<T extends string>(key: string, initial: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      return (localStorage.getItem(key) as T | null) ?? initial;
    } catch {
      return initial;
    }
  });

  const set = useCallback(
    (next: T) => {
      setValue(next);
      try {
        localStorage.setItem(key, next);
      } catch {
        /* storage disabled — the value still works in memory */
      }
    },
    [key],
  );

  return [value, set];
}
