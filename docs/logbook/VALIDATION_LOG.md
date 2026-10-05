# Current verification

5 October 2026. Completion checks for issue #25 / PR #35.
[Scientific result](../optimization/ISSUE25_MATCHED_TARGETS.md) ·
[Archive procedure](../validation/REPRODUCING_RESULTS.md)

The tested PR revision is `756d30d3f39dbe447d46f814c21983c2bd65bd46`.
The scientific producer/evaluator remains clean
`a551289e63e44d7dbae7b5d5a0e5f4b6026db257`; completion edits change documentation
only. A fresh depth-one, single-branch, no-tags clone of the PR checkout supplied
all tracked test inputs. No ignored research outputs were copied into it.

| Check | Result |
| --- | --- |
| Native regression, preserved Python 3.12 environment | 264 passed; eight existing NumPy/netCDF deprecation warnings |
| Dependency-free public tests | 60 passed |
| Documentation, Ruff 0.16.5 and diff whitespace | Pass |
| Hosted CI at the tested PR revision | Core and all six Linux/macOS/Windows public matrix jobs passed |
| Prepared archive manifest | All 6,258 file hashes verified; manifest and summary match the tag annotation |
| Original local outputs | All 6,254 files match the archive byte-for-byte |
| Archived numerical replay | Both targets' field metrics and every action cell/failure reproduced |

Native tests ran in the isolated clone with an empty environment and one native
thread, using the existing serial wrapper that disables optional `mpi4py`.
The direct pytest attempt failed during sandbox MPI initialization before tests
could run. The preserved environment was neither synchronized nor modified.
Ruff used the cached 0.16.5 executable after uv's default cache access was denied.
These checks do not establish MPI support or independent native reproduction.

The prepared archive is commit `05a4511084912fea9bd8d03e81f01018882396b8`,
annotated tag `evidence-issue25-matched-v1`, tag object
`fcbdbe28ba77c2f327546dcb6e01fc9743e5bc07`. It remains local: automatic approval
review rejected publication pending explicit user authority. Remote retrieval
therefore remains unchecked. Original Wouts and upstream validation archives are
maintainer-local. Array replay does not rerun optimization, native tracing or
geometry, and is not physical acceptance or external peer review.

Earlier verification records remain in Git. The experiment's failure cases and
acceptance limits are unchanged; the unresolved physical transfer result meets
the issue's allowance for an inconclusive test, once its evidence is available.
