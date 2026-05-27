import { cli, Strategy } from '@jackwener/opencli/registry';
import {
  gatewayRequest,
  parseAggregate,
  parseFilter,
  parseOrderBy,
  splitCsv,
} from './gateway-client.js';

cli({
  site: 'parquet',
  name: 'query',
  access: 'read',
  description: 'Run a permission-controlled Parquet query through the gateway',
  strategy: Strategy.LOCAL,
  browser: false,
  args: [
    { name: 'dataset', positional: true, required: true, help: 'Dataset id' },
    { name: 'select', help: 'Comma-separated fields' },
    { name: 'where', help: 'Filter expression, repeat with comma for multiple filters' },
    { name: 'group-by', help: 'Comma-separated grouping fields' },
    { name: 'aggregate', help: 'Aggregate expression, repeat with comma: sum:amount:total' },
    { name: 'order-by', help: 'Sort expression, e.g. amount:desc' },
    { name: 'limit', type: 'int', help: 'Maximum result rows' },
  ],
  func: async (args) => {
    const body = { dataset: args.dataset };
    const select = splitCsv(args.select);
    if (select.length > 0) body.select = select;
    const filters = splitCsv(args.where).map(parseFilter);
    if (filters.length > 0) body.filters = filters;
    const groupBy = splitCsv(args['group-by']);
    if (groupBy.length > 0) body.group_by = groupBy;
    const aggregates = splitCsv(args.aggregate).map(parseAggregate);
    if (aggregates.length > 0) body.aggregates = aggregates;
    const orderBy = parseOrderBy(args['order-by']);
    if (orderBy.length > 0) body.order_by = orderBy;
    if (args.limit !== undefined) body.limit = Number(args.limit);

    const payload = await gatewayRequest('/query', { method: 'POST', body });
    return payload.rows || [];
  },
});
