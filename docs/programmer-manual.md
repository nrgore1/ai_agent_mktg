# Programmer manual
`core.py` owns transactions, registries, records, agent preparation, governance and scheduling. `server.py` owns authentication, request validation, same-origin protections, static assets and worker lifecycle. `static/` contains the responsive dependency-free UI. `registry.json` is the initial seed. Existing databases use INSERT OR IGNORE, so editing seeds does not migrate existing rows. Use a reviewed migration for persisted changes.

Run `python3 -m unittest discover -s tests -v` and `python3 -m compileall -q growthpilot` on Ubuntu. No third-party Python dependencies. SQLite transactions use BEGIN IMMEDIATE to serialize approval and execution and avoid double receipts. New external provider work requires its own integration suite and durable outbox; the existing transaction is only correct for the local mock.

Add product-specific permissions before serving multiple users. Add schema migrations before evolving persisted fields. Frontend renders dynamic text using HTML escaping. Never put API tokens in URLs, localStorage, logs or repository files.
