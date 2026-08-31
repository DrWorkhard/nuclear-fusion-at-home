#!/usr/bin/env python3
"""Audit public primary-source locations for an authoritative SQuID-C package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

DOI = "10.1017/S0022377825100974"
TITLE = "A quasi-isodynamic stellarator configuration towards a fusion power plant"
CAMBRIDGE_URL = (
    "https://www.cambridge.org/core/journals/journal-of-plasma-physics/article/"
    "quasiisodynamic-stellarator-configuration-towards-a-fusion-power-plant/"
    "C8A4D1BBC282A9632924B5B85173A6AC"
)
NAME_PATTERN = re.compile(r"squid(?:[-_ ]?c)", re.IGNORECASE)
PROVENANCE_COLUMN_PATTERN = re.compile(
    r"(?:^|[/_.])(name|source|citation|doi|paper|reference)(?:$|[/_.])", re.IGNORECASE
)
USER_AGENT = "fusion-baselines-squid-c-availability-audit/1"


def _request(url: str) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json, text/html;q=0.9", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), dict(response.headers.items())


def _json(url: str) -> tuple[Any, str]:
    payload, _ = _request(url)
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def _encoded_query(base_url: str, parameters: dict[str, str]) -> str:
    return f"{base_url}?{urllib.parse.urlencode(parameters)}"


def _next_link(headers: dict[str, str]) -> str | None:
    for key, value in headers.items():
        if key.lower() != "link":
            continue
        for entry in value.split(","):
            match = re.match(r'\s*<([^>]+)>;\s*rel="next"', entry)
            if match:
                return match.group(1)
    return None


def _audit_zenodo() -> dict[str, Any]:
    queries = {
        "configuration_name": '"SQuID-C"',
        "article_doi": f'"{DOI}"',
        "article_title": f'"{TITLE}"',
    }
    results: dict[str, Any] = {}
    for label, query in queries.items():
        url = _encoded_query("https://zenodo.org/api/records/", {"q": query, "size": "25"})
        response, response_hash = _json(url)
        results[label] = {
            "query": query,
            "url": url,
            "hits_total": response["hits"]["total"],
            "response_sha256": response_hash,
        }
    return {
        "queries": results,
        "all_zero_hits": all(r["hits_total"] == 0 for r in results.values()),
    }


def _audit_datacite() -> dict[str, Any]:
    queries = {
        "related_article_doi": f'relatedIdentifiers.relatedIdentifier:"{DOI}"',
        "article_title": f'titles.title:"{TITLE}"',
    }
    results: dict[str, Any] = {}
    for label, query in queries.items():
        url = _encoded_query("https://api.datacite.org/dois", {"query": query, "page[size]": "25"})
        response, response_hash = _json(url)
        results[label] = {
            "query": query,
            "url": url,
            "hits_total": response["meta"]["total"],
            "dois": [entry["id"] for entry in response["data"]],
            "response_sha256": response_hash,
        }
    return {
        "queries": results,
        "all_zero_hits": all(r["hits_total"] == 0 for r in results.values()),
    }


def _audit_github() -> dict[str, Any]:
    repos_url = "https://api.github.com/orgs/proximafusion/repos?per_page=100&type=public"
    repositories, repos_hash = _json(repos_url)
    repo_records = []
    total_paths = 0
    path_matches = []
    for repo in repositories:
        tree_url = (
            f"https://api.github.com/repos/proximafusion/{repo['name']}/git/trees/"
            f"{repo['default_branch']}?recursive=1"
        )
        tree, tree_hash = _json(tree_url)
        paths = [entry["path"] for entry in tree.get("tree", [])]
        matches = [path for path in paths if NAME_PATTERN.search(path)]
        total_paths += len(paths)
        path_matches.extend(f"{repo['name']}:{path}" for path in matches)
        repo_records.append(
            {
                "name": repo["name"],
                "url": repo["html_url"],
                "default_branch": repo["default_branch"],
                "tree_sha": tree.get("sha"),
                "tree_response_sha256": tree_hash,
                "tree_truncated": tree.get("truncated", False),
                "path_count": len(paths),
                "matching_paths": matches,
            }
        )
    return {
        "organization": "proximafusion",
        "repositories_url": repos_url,
        "repositories_response_sha256": repos_hash,
        "repository_count": len(repo_records),
        "total_paths": total_paths,
        "all_trees_complete": all(not record["tree_truncated"] for record in repo_records),
        "matching_paths": path_matches,
        "repositories": repo_records,
        "scope_limit": (
            "All public repository paths were searched. Blob contents were not exhaustively "
            "searched because unauthenticated GitHub code search is unavailable."
        ),
    }


def _paginated_hugging_face_tree(dataset_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    # Hugging Face's route parser expects the namespace separator literally.
    encoded_id = urllib.parse.quote(dataset_id, safe="/")
    url = (
        f"https://huggingface.co/api/datasets/{encoded_id}/tree/main"
        "?recursive=true&expand=false&limit=1000"
    )
    entries: list[dict[str, Any]] = []
    response_hashes: list[str] = []
    while url is not None:
        payload, headers = _request(url)
        entries.extend(json.loads(payload))
        response_hashes.append(hashlib.sha256(payload).hexdigest())
        url = _next_link(headers)
    return entries, response_hashes


def _audit_hugging_face() -> dict[str, Any]:
    datasets_url = "https://huggingface.co/api/datasets?author=proxima-fusion&limit=100&full=true"
    datasets, datasets_hash = _json(datasets_url)
    dataset_records = []
    all_path_matches = []
    for dataset in datasets:
        entries, tree_hashes = _paginated_hugging_face_tree(dataset["id"])
        paths = [entry["path"] for entry in entries]
        matches = [path for path in paths if NAME_PATTERN.search(path)]
        all_path_matches.extend(f"{dataset['id']}:{path}" for path in matches)
        dataset_records.append(
            {
                "id": dataset["id"],
                "url": f"https://huggingface.co/datasets/{dataset['id']}",
                "revision_sha": dataset["sha"],
                "path_count": len(paths),
                "matching_paths": matches,
                "tree_page_response_sha256": tree_hashes,
            }
        )

    schema_url = (
        "https://datasets-server.huggingface.co/first-rows?"
        "dataset=proxima-fusion%2Fcoilstellaration&config=results&split=train"
    )
    schema, schema_hash = _json(schema_url)
    feature_names = [feature["name"] for feature in schema["features"]]
    provenance_columns = [
        feature for feature in feature_names if PROVENANCE_COLUMN_PATTERN.search(feature)
    ]
    return {
        "organization": "proxima-fusion",
        "datasets_url": datasets_url,
        "datasets_response_sha256": datasets_hash,
        "dataset_count": len(dataset_records),
        "matching_paths": all_path_matches,
        "datasets": dataset_records,
        "coilstellaration_results_schema": {
            "url": schema_url,
            "response_sha256": schema_hash,
            "feature_count": len(feature_names),
            "human_provenance_columns": provenance_columns,
            "boundary_link_column": "constellaration_boundary_id",
        },
        "scope_limit": (
            "Every public dataset path was searched. Multi-gigabyte row payloads were not "
            "exhaustively scanned; CoilStellaration exposes opaque boundary IDs and no human "
            "paper/DOI/source column in its results schema, so an anonymous row cannot be "
            "authoritatively mapped to SQuID-C."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    article_payload, _ = _request(CAMBRIDGE_URL)
    article_text = article_payload.decode("utf-8", errors="replace")
    crossref_url = f"https://api.crossref.org/works/{urllib.parse.quote(DOI, safe='')}"
    crossref, crossref_hash = _json(crossref_url)
    crossref_message = crossref["message"]

    github = _audit_github()
    hugging_face = _audit_hugging_face()
    zenodo = _audit_zenodo()
    datacite = _audit_datacite()
    no_direct_release_found = all(
        (
            "supplementaryMaterials:[]" in article_text,
            len(crossref_message.get("relation", {})) == 0,
            github["all_trees_complete"],
            not github["matching_paths"],
            not hugging_face["matching_paths"],
            not hugging_face["coilstellaration_results_schema"]["human_provenance_columns"],
            zenodo["all_zero_hits"],
            datacite["all_zero_hits"],
        )
    )
    evidence = {
        "schema_version": 1,
        "audit_date": args.as_of.isoformat(),
        "subject": {"name": "SQuID-C", "doi": DOI, "title": TITLE},
        "publisher": {
            "article_url": CAMBRIDGE_URL,
            "article_html_sha256": hashlib.sha256(article_payload).hexdigest(),
            "empty_supplementary_materials_metadata": "supplementaryMaterials:[]" in article_text,
        },
        "crossref": {
            "url": crossref_url,
            "response_sha256": crossref_hash,
            "registered_title": crossref_message["title"][0],
            "relations": crossref_message.get("relation", {}),
            "relation_count": len(crossref_message.get("relation", {})),
        },
        "zenodo": zenodo,
        "datacite": datacite,
        "github": github,
        "hugging_face": hugging_face,
        "required_authoritative_artifacts_not_located": [
            "fixed-boundary finite-beta target VMEC input and converged output",
            "coil-generated free-boundary VMEC input and converged output",
            "complete coil geometry or winding volumes with signed currents and symmetry",
            "MAKEGRID response file or an exact reproducible generation recipe",
            "pressure and current profiles, physical scale, and field normalization",
            "the run settings needed to reproduce the paper-level coil and physics metrics",
        ],
        "assessment": {
            "authoritative_machine_readable_package_located": False,
            "public_absence_audit_passed": no_direct_release_found,
            "statement": (
                "No publicly identified authoritative SQuID-C machine package was located in "
                "the audited primary-source channels as of the audit date. This records search "
                "coverage and is not proof that no unpublished, anonymous, or unindexed data exist."
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if no_direct_release_found else 2


if __name__ == "__main__":
    raise SystemExit(main())
