import { createServer } from 'node:http';
import { mkdir, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { spawn } from 'node:child_process';
import { cli, Strategy } from '@jackwener/opencli/registry';
import { gatewayRequest } from './gateway-client.js';

const DEFAULT_REDIRECT_URI = 'http://127.0.0.1:8765/callback';
const DEFAULT_TOKEN_PATH = join(homedir(), '.parquet-gateway', 'token.json');

cli({
  site: 'parquet',
  name: 'login',
  access: 'read',
  description: 'Log in with Feishu and save a gateway token',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [
    { name: 'code', positional: true, required: false, help: 'Feishu OAuth authorization code' },
    { name: 'redirect-uri', help: 'Feishu redirect URI used for the authorization code' },
    { name: 'auth-url', help: 'Feishu authorization URL; defaults to PARQUET_FEISHU_AUTH_URL' },
    { name: 'token-path', help: 'Where to save the gateway token JSON' },
    { name: 'timeout', type: 'int', default: 180, help: 'Seconds to wait for local callback' },
  ],
  columns: ['token_path', 'token_type', 'expires_in', 'PARQUET_GATEWAY_TOKEN'],
  func: async (args) => {
    const redirectUri = args['redirect-uri'] || process.env.PARQUET_FEISHU_REDIRECT_URI || DEFAULT_REDIRECT_URI;
    const code = args.code || await loginViaBrowser({
      authUrl: args['auth-url'] || process.env.PARQUET_FEISHU_AUTH_URL,
      redirectUri,
      timeoutSeconds: Number(args.timeout || 180),
    });
    const payload = await gatewayRequest('/auth/feishu/exchange', {
      method: 'POST',
      body: { code, redirect_uri: redirectUri },
      auth: false,
    });
    const tokenPath = args['token-path'] || process.env.PARQUET_GATEWAY_TOKEN_PATH || DEFAULT_TOKEN_PATH;
    await saveGatewayToken(tokenPath, payload);
    return [{
      token_path: tokenPath,
      token_type: payload.token_type,
      expires_in: payload.expires_in,
      PARQUET_GATEWAY_TOKEN: payload.access_token,
    }];
  },
});

async function loginViaBrowser({ authUrl, redirectUri, timeoutSeconds }) {
  if (!authUrl) {
    throw new Error('PARQUET_FEISHU_AUTH_URL or --auth-url is required when code is not provided');
  }
  const callbackPromise = waitForCallbackCode({ redirectUri, timeoutSeconds });
  openBrowser(authUrl);
  return await callbackPromise;
}

function waitForCallbackCode({ redirectUri, timeoutSeconds }) {
  const parsed = new URL(redirectUri);
  const host = parsed.hostname;
  const port = Number(parsed.port || 80);
  const expectedPath = parsed.pathname;

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      server.close();
      reject(new Error(`Timed out waiting for Feishu callback after ${timeoutSeconds}s`));
    }, timeoutSeconds * 1000);

    const server = createServer((req, res) => {
      try {
        const url = new URL(req.url || '/', redirectUri);
        if (url.pathname !== expectedPath) {
          res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end('Not Found');
          return;
        }
        const error = url.searchParams.get('error');
        if (error) throw new Error(`Feishu authorization failed: ${error}`);
        const code = url.searchParams.get('code');
        if (!code) throw new Error('Feishu callback did not include code');
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end('<html><body>Parquet Gateway login complete. You can close this window.</body></html>');
        clearTimeout(timer);
        server.close();
        resolve(code);
      } catch (err) {
        clearTimeout(timer);
        server.close();
        reject(err);
      }
    });

    server.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });
    server.listen(port, host);
  });
}

function openBrowser(url) {
  const platform = process.platform;
  const command = platform === 'win32' ? 'cmd' : platform === 'darwin' ? 'open' : 'xdg-open';
  const args = platform === 'win32' ? ['/c', 'start', '', url] : [url];
  const child = spawn(command, args, { detached: true, stdio: 'ignore' });
  child.unref();
}

async function saveGatewayToken(tokenPath, payload) {
  await mkdir(dirname(tokenPath), { recursive: true });
  await writeFile(tokenPath, `${JSON.stringify({
    access_token: payload.access_token,
    token_type: payload.token_type,
    expires_in: payload.expires_in,
    saved_at: new Date().toISOString(),
  }, null, 2)}\n`, 'utf-8');
}
