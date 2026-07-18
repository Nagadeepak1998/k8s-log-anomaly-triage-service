# Deployment Anomaly Trend Review: embedding-platform-july-releases

- Status: `page`
- Reviewed deployments: `4`
- Anomalous deployments: `3`
- Unowned deployments: `0`
- Recurring classes: `dependency_timeout`

## Deployment Results

| Deployment | Service | Environment | Owner | Risk | Class |
| --- | --- | --- | --- | ---: | --- |
| embedding-api-2026-07-10.1 | embedding-api | staging | ml-platform-oncall | 0.00 | no_clear_anomaly |
| embedding-api-2026-07-14.2 | embedding-api | staging | ml-platform-oncall | 24.30 | dependency_timeout |
| embedding-api-2026-07-17.3 | embedding-api | staging | ml-platform-oncall | 24.30 | dependency_timeout |
| reranker-api-2026-07-17.1 | reranker-api | staging | ranking-platform-oncall | 29.70 | memory_pressure |

## Owner Routing

- `ml-platform-oncall`: 2 deployment(s), services embedding-api, classes dependency_timeout
- `ranking-platform-oncall`: 1 deployment(s), services reranker-api, classes memory_pressure

## Recommended Actions

- Route each anomaly group to its workload owner with deployment evidence.
- Investigate recurring dependency_timeout across deployment boundaries.
