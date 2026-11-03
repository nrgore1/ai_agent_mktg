# Read saved private VPS receipts. Does not rerun tests, infer, email or deploy.
import json
from pathlib import Path
root = Path.home() / "agentvire-launch-qa-20261027"
names = ["core-final-20261028.json", "postmark-acceptance-20261028.json", "individual-market-acceptance-20261028.json", "institutional-market-acceptance-20261028.json", "speech-playback-final-20261028.json", "ora-smtp-acceptance-20261028.json", "liqmint-local-kimi-20261028.json", "application-local-kimi-20261028.json"]
if __name__ == "__main__":
    result = {name: json.loads((root / name).read_text()) for name in names}
    print(json.dumps({"mode": "saved_evidence_not_fresh_execution", "launch_ready": False, "receipts": result}, indent=2))
