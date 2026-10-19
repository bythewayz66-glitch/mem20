/// <reference types="vite/client" />

/**
 * Typed access to the env vars this app actually reads.
 *
 * Declaring them turns a typo (`VITE_SOURCE_MOD`) into a compile error instead
 * of a silently undefined value that flips every surface to its fallback.
 */
interface ImportMetaEnv {
  /** 'snapshot' (default) lets a surface fall back to a labelled capture; 'live' forbids it. */
  readonly VITE_SOURCE_MODE?: 'live' | 'snapshot';
  /** teamz chat transport: 'mock' answers locally, 'live' calls agent endpoints. */
  readonly VITE_API_MODE?: 'mock' | 'live';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
