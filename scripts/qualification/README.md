# Isolated product qualification runners

These are operator-run product component checks, separate from AgentVire unit tests. Never run them against a production database or attach production environment files. The Docker runners use exact currently deployed image IDs, no network, read-only filesystems, temporary storage and synthetic settings. Live service names are inspected only to identify images. The findings do not automatically certify a replacement image after a product deployment.

On the authorized VPS:

1. Run `build_test_runtime.py` to create the test-only Jodibana pytest layer from the deployed base image. This step downloads pinned test tooling; the tests themselves have no network.
2. Run `run_deployed_tests.py` for the bundled LiqMint and Jodibana suites. The Institutional report directory is temporary container storage only.
3. Keep the three `component_*.py` files next to `build_components.py`; run the builder and then generated `run_components.py` for OraToPlus, Memoire and WeddingOS. Selected database and provider boundaries are mocked: read the per-test implementation and coverage limits.
4. Preserve logs and exact image references. Current runners write dated evidence under the operator home directory. Review failed assertions as failures, not expected passes. Product lifecycle checks require additional safe sandbox/browser fixtures.
5. Construct all 17 product/category records following `growthpilot/qualification.py`. Run `python -m growthpilot.qualification --db <authorized-AgentVire-db> --report <verified-report.json>` only after reviewing the evidence and current strategy revision. The CLI records evidence and can approve only fully qualified technical tasks; it cannot activate pricing, commissions or campaigns.

The checked-in 1 November results include five real component failures, intentionally retained in the product backlog. Re-running the component scripts alone does not update AgentVire or approve a task. The seven-day freshness check applies when importing evidence; later image or scope changes require a new run.
