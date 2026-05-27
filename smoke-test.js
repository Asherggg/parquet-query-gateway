import { cli, Strategy } from '@jackwener/opencli/registry';
import { gatewayRequest } from './gateway-client.js';

cli({
  site: 'parquet',
  name: 'smoke-test',
  access: 'read',
  description: 'Check gateway health and run a one-row query',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [],
  columns: ['ok', 'dataset', 'visible_dataset_count', 'first_column', 'query_row_count'],
  func: async () => {
    const health = await gatewayRequest('/health', { auth: false });
    const datasetsPayload = await gatewayRequest('/datasets');
    const datasets = datasetsPayload.datasets || [];
    if (datasets.length === 0) {
      throw new Error('Gateway returned no visible datasets');
    }
    const dataset = datasets[0].id;
    const schema = await gatewayRequest(`/datasets/${encodeURIComponent(dataset)}/schema`);
    const columns = schema.columns || [];
    if (columns.length === 0) {
      throw new Error(`Dataset ${dataset} has no visible columns`);
    }
    const query = await gatewayRequest('/query', {
      method: 'POST',
      body: { dataset, select: [columns[0]], limit: 1 },
    });
    return [{
      ok: health.status === 'ok',
      dataset,
      visible_dataset_count: datasets.length,
      first_column: columns[0],
      query_row_count: query.row_count || 0,
    }];
  },
});
