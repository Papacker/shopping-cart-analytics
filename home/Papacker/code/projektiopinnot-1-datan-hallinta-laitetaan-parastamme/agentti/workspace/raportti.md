```json
{
  "name": "query_duckdb",
  "arguments": {
    "sql": "SELECT sc.description, COUNT(v.visit_id) AS kaynteja, ROUND(AVG(v.duration_seconds) / 60, 1) AS keski_kesto_min FROM Visit v JOIN ShoppingCart sc ON v.node_id = sc.node_id GROUP BY sc.description ORDER BY kaynteja DESC"
  }
}
```