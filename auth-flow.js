import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { spawn } from 'node:child_process';

export const DEFAULT_REDIRECT_URI = 'http://127.0.0.1:8765/callback';
export const DEFAULT_TOKEN_PATH = join(homedir(), '.parquet-gateway', 'token.json');

export function tokenPath() {
  return process.env.PARQUET_GATEWAY_TOKEN_PATH || DEFAULT_TOKEN_PATH;
}

export async function readSavedGatewayToken(path = tokenPath()) {
  try {
    const raw = await readFile(path, 'utf-8');
    const payload = JSON.parse(raw);
    return payload.access_token || '';
  } catch (err) {
    if (err?.code === 'ENOENT') return '';
    throw err;
  }
}

export async function discoverFeishuAuthUrl({ gatewayUrl, redirectUri }) {
  if (process.env.PARQUET_FEISHU_AUTH_URL) {
    return process.env.PARQUET_FEISHU_AUTH_URL;
  }
  const url = new URL('/auth/feishu/authorize-url', gatewayUrl);
  url.searchParams.set('redirect_uri', redirectUri);
  const response = await fetch(url);
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = payload?.error?.message || payload?.detail || response.statusText;
    throw new Error(`Feishu login is not available from gateway: ${message}`);
  }
  if (!payload.auth_url) {
    throw new Error('Gateway did not return a Feishu authorization URL');
  }
  return payload.auth_url;
}

export async function loginWithFeishu({
  gatewayUrl,
  authUrl,
  redirectUri = process.env.PARQUET_FEISHU_REDIRECT_URI || DEFAULT_REDIRECT_URI,
  timeoutSeconds = 180,
  savePath = tokenPath(),
  pollIntervalMs = 2000,
} = {}) {
  if (!authUrl && !process.env.PARQUET_FEISHU_AUTH_URL && process.env.PARQUET_USE_LOCAL_CALLBACK !== '1') {
    try {
      return await loginWithGatewaySession({
        gatewayUrl,
        timeoutSeconds,
        savePath,
        pollIntervalMs,
      });
    } catch (err) {
      if (!err?.gatewaySessionUnavailable) throw err;
      console.error(`${err.message}\nFalling back to local browser callback login.`);
    }
  }
  const actualAuthUrl = authUrl || await discoverFeishuAuthUrl({ gatewayUrl, redirectUri });
  const code = await loginViaBrowser({
    authUrl: actualAuthUrl,
    redirectUri,
    timeoutSeconds,
  });
  const payload = await exchangeFeishuCode({
    gatewayUrl,
    code,
    redirectUri,
  });
  await saveGatewayToken(savePath, payload);
  return payload;
}

export async function loginWithGatewaySession({
  gatewayUrl,
  timeoutSeconds = 180,
  savePath = tokenPath(),
  pollIntervalMs = 2000,
} = {}) {
  const sessionUrl = new URL('/auth/feishu/login-session', gatewayUrl);
  const sessionResponse = await fetch(sessionUrl, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  const sessionPayload = await readJsonResponse(sessionResponse);
  if (!sessionResponse.ok) {
    const message = sessionPayload?.error?.message || sessionPayload?.detail || sessionResponse.statusText;
    const err = new Error(`Gateway-hosted Feishu login is not available: ${message}`);
    if ([404, 405, 501].includes(sessionResponse.status)) err.gatewaySessionUnavailable = true;
    throw err;
  }
  if (!sessionPayload.session_id || !sessionPayload.auth_url) {
    throw new Error('Gateway did not return a Feishu login session');
  }
  console.error([
    'Feishu login is waiting for gateway callback.',
    '',
    'Trying to open your default browser for Feishu authorization.',
    'If no browser opens within 5 seconds, copy this authorization URL into your browser:',
    sessionPayload.auth_url,
    '',
    `After login, Feishu should return to ${sessionPayload.redirect_uri || 'the gateway callback URL'}.`,
    'This terminal will continue waiting and save the gateway token automatically.',
    '',
    'Keep this command running until it prints the saved token path.',
    `If this command is interrupted after browser authorization, recover with: opencli parquet login --session-id ${sessionPayload.session_id}`,
    'You can also paste the full browser callback URL with: opencli parquet login --callback-url "<callback-url>"',
  ].join('\n'));
  openBrowser(sessionPayload.auth_url);

  const deadline = Date.now() + timeoutSeconds * 1000;
  let nextNoticeAt = Date.now() + Math.min(15000, Math.max(1000, pollIntervalMs));
  while (Date.now() < deadline) {
    const pollUrl = new URL(`/auth/feishu/login-session/${encodeURIComponent(sessionPayload.session_id)}`, gatewayUrl);
    const pollResponse = await fetch(pollUrl, { headers: { Accept: 'application/json' } });
    const pollPayload = await readJsonResponse(pollResponse);
    if (!pollResponse.ok) {
      const message = pollPayload?.error?.message || pollPayload?.detail || pollResponse.statusText;
      throw new Error(`Gateway login session failed: ${message}`);
    }
    if (pollPayload.status === 'complete') {
      await saveGatewayToken(savePath, pollPayload);
      return pollPayload;
    }
    if (pollPayload.status === 'error') {
      const details = formatDetails(pollPayload.details);
      const detailsSuffix = details ? `\n${details}` : '';
      throw new Error(`Feishu login failed: ${pollPayload.message || 'unknown error'}${detailsSuffix}`);
    }
    if (Date.now() >= nextNoticeAt) {
      const expiresIn = pollPayload.expires_in === undefined ? '' : ` session_expires_in=${pollPayload.expires_in}s`;
      console.error(`Still waiting for Feishu browser authorization... session_id=${sessionPayload.session_id}${expiresIn}`);
      nextNoticeAt = Date.now() + 15000;
    }
    await sleep(pollIntervalMs);
  }
  throw new Error([
    `Timed out waiting for Feishu gateway login after ${timeoutSeconds}s.`,
    `If the browser already completed authorization, recover with: opencli parquet login --session-id ${sessionPayload.session_id}`,
    'Or paste the full browser callback URL with: opencli parquet login --callback-url "<callback-url>"',
  ].join('\n'));
}

export async function completeGatewayLoginFromCallbackUrl({
  gatewayUrl,
  callbackUrl,
  savePath = tokenPath(),
} = {}) {
  if (!callbackUrl) throw new Error('--callback-url is required');
  let parsed;
  try {
    parsed = new URL(callbackUrl);
  } catch {
    throw new Error('Invalid Feishu callback URL');
  }
  const sessionId = parsed.searchParams.get('state');
  if (!sessionId) {
    throw new Error('Feishu callback URL does not include state; cannot recover gateway login session');
  }
  return await completeGatewayLoginSession({ gatewayUrl, sessionId, savePath });
}

export async function completeGatewayLoginSession({
  gatewayUrl,
  sessionId,
  savePath = tokenPath(),
} = {}) {
  if (!sessionId) throw new Error('--session-id is required');
  const pollUrl = new URL(`/auth/feishu/login-session/${encodeURIComponent(sessionId)}`, gatewayUrl);
  const response = await fetch(pollUrl, { headers: { Accept: 'application/json' } });
  const payload = await readJsonResponse(response);
  if (!response.ok) {
    const message = payload?.error?.message || payload?.detail || response.statusText;
    throw new Error(`Gateway login session failed: ${message}`);
  }
  if (payload.status === 'complete') {
    await saveGatewayToken(savePath, payload);
    return payload;
  }
  if (payload.status === 'error') {
    const details = formatDetails(payload.details);
    const detailsSuffix = details ? `\n${details}` : '';
    throw new Error(`Feishu login failed: ${payload.message || 'unknown error'}${detailsSuffix}`);
  }
  if (payload.status === 'pending') {
    throw new Error([
      `Feishu login session ${sessionId} is still pending.`,
      'Complete browser authorization first, then run this recovery command again.',
    ].join('\n'));
  }
  throw new Error(`Feishu login session ${sessionId} is not complete`);
}

export async function exchangeFeishuCode({ gatewayUrl, code, redirectUri }) {
  const response = await fetch(new URL('/auth/feishu/exchange', gatewayUrl), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code, redirect_uri: redirectUri }),
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = payload?.error?.message || payload?.detail || response.statusText;
    throw new Error(`Gateway HTTP ${response.status}: ${message}`);
  }
  return payload;
}

async function readJsonResponse(response) {
  const text = await response.text();
  return text ? JSON.parse(text) : {};
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatDetails(details) {
  if (!details || typeof details !== 'object') return '';
  const lines = Object.entries(details)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `  ${key}: ${value}`);
  return lines.length ? `Details:\n${lines.join('\n')}` : '';
}

export async function loginViaBrowser({ authUrl, redirectUri, timeoutSeconds }) {
  if (!authUrl) {
    throw new Error('PARQUET_FEISHU_AUTH_URL, --auth-url, or gateway Feishu auth configuration is required when code is not provided');
  }
  const callbackPromise = waitForCallbackCode({ redirectUri, timeoutSeconds });
  console.error([
    'Feishu login is waiting for a browser callback.',
    '',
    'Trying to open your default browser for Feishu authorization.',
    'If no browser opens within 5 seconds, copy this authorization URL into your browser:',
    authUrl,
    '',
    `After login, the browser should return to ${redirectUri}.`,
    'If that page cannot be reached but the address bar contains code=..., copy that code and run:',
    '  opencli parquet login "<code>"',
  ].join('\n'));
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
  if (process.env.PARQUET_DISABLE_BROWSER_OPEN === '1') return;
  const platform = process.platform;
  const command = platform === 'win32' ? 'powershell.exe' : platform === 'darwin' ? 'open' : 'xdg-open';
  const args = platform === 'win32'
    ? ['-NoProfile', '-Command', 'Start-Process', '-FilePath', url]
    : [url];
  const child = spawn(command, args, { detached: true, stdio: 'ignore' });
  child.unref();
}

export async function saveGatewayToken(path, payload) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify({
    access_token: payload.access_token,
    token_type: payload.token_type,
    expires_in: payload.expires_in,
    saved_at: new Date().toISOString(),
  }, null, 2)}\n`, 'utf-8');
}
