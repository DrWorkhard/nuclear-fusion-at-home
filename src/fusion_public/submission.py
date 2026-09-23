"""Optional contribution metadata, never an allowlist of permitted research."""

from .data import require


def validate(document):
    require(type(document) is dict, "Contribution record must be a JSON object")
    required = {"schema_version", "title", "contribution", "evidence", "limitations"}
    optional = {"compute", "related_hint", "authors", "tools", "reproduction"}
    require(required <= set(document) <= required | optional,
            "Required: schema_version,title,contribution,evidence,limitations; compute is optional")
    require(type(document["schema_version"]) is int and document["schema_version"] == 1,
            "Contribution schema_version1 required")
    for key in required - {"schema_version"}:
        require(type(document[key]) is str and 0 < len(document[key].strip()) <= 20000,
                f"A nonempty readable {key} is required (up to20000 characters)")
    for key in optional:
        if key in document:
            require(document[key] is None or type(document[key]) is str
                    and len(document[key]) <= 20000, f"Optional {key}: text or null")
    # No cost threshold, hint registry lookup, automatic shell or link execution.
    return dict(schema_version=1, contribution_record_valid=True,
                compute_disclosed=bool(document.get("compute")),
                requested_topic_required=False, scientific_acceptance=False)
