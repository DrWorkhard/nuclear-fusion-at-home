import hashlib
import json
from pathlib import Path


def test_frozen_warmstart_bytes_and_honest_producer_lineage():
    root = Path(__file__).resolve().parents[1]
    fixture = root / "fixtures/rejected-lpqa-warmstart"
    data = (fixture / "field.json").read_bytes()
    assert (
        hashlib.sha256(data).hexdigest()
        == "ef38a96aa6820de08d187f6362645b5450f009034706b06b2722566da9631e8c"
    )
    assert data.endswith(b"\n")
    assert (
        hashlib.sha256(data[:-1]).hexdigest()
        == "7ae1b1968b8ca34fa94cc0e67cfad41577219ed43bcd902b695c7b7cc04ecd2e"
    )
    assert json.loads(data)["@class"] == "SIMSON"
    producer = json.loads((fixture / "producer_provenance.json").read_text())
    assert producer["repository"]["commit"] is None
    assert producer["repository"]["dirty"] is True
