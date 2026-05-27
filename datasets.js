import { cli, Strategy } from '@jackwener/opencli/registry';
import { gatewayRequest } from './gateway-client.js';

cli({
  site: 'parquet',
  name: 'datasets',
  access: 'read',
  description: 'List Parquet datasets visible to the current token',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [],
  columns: ['id', 'description', 'columns'],
  func: async () => {
    const payload = await gatewayRequest('/datasets');
    return payload.datasets || [];
  },
});
