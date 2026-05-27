import { cli, Strategy } from '@jackwener/opencli/registry';
import { gatewayRequest } from './gateway-client.js';

cli({
  site: 'parquet',
  name: 'schema',
  access: 'read',
  description: 'Show visible columns for a Parquet dataset',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [
    { name: 'dataset', positional: true, required: true, help: 'Dataset id' },
  ],
  columns: ['dataset', 'column'],
  func: async (args) => {
    const payload = await gatewayRequest(`/datasets/${encodeURIComponent(args.dataset)}/schema`);
    return (payload.columns || []).map((column) => ({ dataset: payload.dataset, column }));
  },
});
