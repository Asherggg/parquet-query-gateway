import { cli, Strategy } from '@jackwener/opencli/registry';
import { gatewayRequest } from './gateway-client.js';

cli({
  site: 'parquet',
  name: 'login',
  access: 'read',
  description: 'Exchange a Feishu OAuth code for a gateway token',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [
    { name: 'code', positional: true, required: true, help: 'Feishu OAuth authorization code' },
    { name: 'redirect-uri', help: 'Feishu redirect URI used for the authorization code' },
  ],
  columns: ['access_token', 'token_type', 'expires_in'],
  func: async (args) => {
    const redirectUri = args['redirect-uri'] || process.env.PARQUET_FEISHU_REDIRECT_URI || 'http://127.0.0.1:8765/callback';
    const payload = await gatewayRequest('/auth/feishu/exchange', {
      method: 'POST',
      body: { code: args.code, redirect_uri: redirectUri },
    });
    return [{
      access_token: payload.access_token,
      token_type: payload.token_type,
      expires_in: payload.expires_in,
      PARQUET_GATEWAY_TOKEN: payload.access_token,
    }];
  },
});
