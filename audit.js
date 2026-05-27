import { cli, Strategy } from '@jackwener/opencli/registry';
import { gatewayRequest } from './gateway-client.js';

cli({
  site: 'parquet',
  name: 'audit',
  access: 'read',
  description: 'Show recent gateway audit events; requires admin role',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [
    { name: 'limit', type: 'int', default: 100, help: 'Maximum audit events' },
  ],
  columns: ['ts', 'user_id', 'dataset', 'action', 'allowed', 'reason', 'row_count', 'duration_ms'],
  func: async (args) => {
    const limit = Number(args.limit || 100);
    const payload = await gatewayRequest(`/admin/audit?limit=${encodeURIComponent(limit)}`);
    return payload.events || [];
  },
});
