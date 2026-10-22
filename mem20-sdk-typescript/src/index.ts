/**
 * @mem20/sdk — TypeScript client for the mem20 MCP server.
 * Protocol: JSON-RPC 2.0 over stdio, MCP revision 2025-06-18.
 */

export { Mem20Client } from './client.js';
export { Mem20Config, type Mem20ConfigOptions } from './config.js';
export {
  Mem20Error,
  ConfigurationError,
  TransportError,
  ToolError,
} from './errors.js';
export { VERSION, PROTOCOL_VERSION, SERVER_VERSION } from './version.js';
