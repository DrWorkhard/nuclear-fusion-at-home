# Community data readiness v1

**Decision:** external geometry coverage warrants reuse before generating more
near-seed samples. Metadata supports considering a boundary-to-vacuum-metric
pilot; it does **not** establish readiness for a joint plasma/coil benefit
surrogate or an unseen-family benchmark. This is a partial contribution to
[#41](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/41), building on
[Lehner's lineage inventory](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/41#issuecomment-5991042833),
not a dataset release.

## Obtainable sources and compatibility

Inventory date: 7 October 2026. Counts below are publisher-reported records,
not measured independent families. Only metadata, documentation and source text
were inspected; no community dataset or fetched code was executed.

| Immutable source | Representation, labels and readiness limits | Rights / availability |
| --- | --- | --- |
| [QUASR v4, DOI 10.5281/zenodo.13717741](https://zenodo.org/records/13717741) | About 370,000 QA/QH vacuum devices with coils, in SIMSOPT/VMEC formats. [Producer paper v2](https://arxiv.org/html/2409.04826v2) scans aspect ratio, iota, coil length and field periods at 1 m major radius. QS quality is not our QI/action or coil-fit error label. Exact coefficient/current conventions, per-record fidelity, ancestry and failure completeness remain uninspected. | [Record API](https://zenodo.org/api/records/13717741) declares MIT; Giuliani credit retained. `QUASR_08072024.tar.gz`: 12,688,330,726 bytes, published MD5 `129b9e6e4a5a7106bd114551d1c80dea`, not downloaded/verified. Old length fields denote **thresholds**, not measured lengths. |
| [ConStellaration dataset `8da71572eb63ce93e77ce89bec0d7c30b7eba89e`](https://huggingface.co/datasets/proxima-fusion/constellaration/blob/8da71572eb63ce93e77ce89bec0d7c30b7eba89e/README.md) | Card reports 182,222 default rows: QI-like R/Z boundary Fourier coefficients, NFP, generation settings, vacuum ideal-MHD metrics and Wout IDs; separate 1–5% beta variants. Error flags exist. Inspected schema does not supply paired coil/current or realized-coil benefit labels. Neither row independence nor label completeness was checked. | Card declares MIT (Proxima Fusion); no separate dataset `LICENSE` file obtained (404). Parquet/Wout locations are published at the pinned revision; payload hashes and joins remain unverified. |
| [Public case at `33e6763`](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/33e6763010ce66f3da07426b5048929e9a14143f/examples/clear-coil-samples-v1) | Reference401 family; named Cartesian order-5 coil coefficients in metres, signed amperes, sparse fixed-current B/A targets and manifest. Public scores are not dense flux-normalized labels. Existing candidate lineage count is Lehner's evidence, not new coverage. | [Packet credits](../../examples/clear-coil-samples-v1/README.md): CC BY 4.0, Goodman DOI 10.5281/zenodo.7220257; code MIT. Committed packet obtainable without native inputs. |
| [Matched archive `05a4511`](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/05a4511084912fea9bd8d03e81f01018882396b8/evidence/issue25-matched-v1) (`evidence-issue25-matched-v1`) | Producer `a551289`; reference401 and its selected401 descendant share a coil seed. Dense normalized field/action arrays, trials and failures are obtainable; wide action labels remain incomplete. This is related-target coverage, not two demonstrated independent families. Original Wouts remain local-only. | Archive credits Goodman/CC BY 4.0 and derived calculations; it does not separately state a blanket archive-data license. Retain attribution and resolve redistribution scope before repackaging; source MIT does not replace data rights. |

## Minimum pilot contract and split

Keep QS, ideal QI, target-launch action and realized-coil diagnostics as distinct
tasks. Bind every imported label to evaluator/dependency versions, physical
scale, signed currents, normalization, grids/weights and search versus verification
fidelity. [Pinned ConStellaration tool v0.3.0](https://github.com/proximafusion/constellaration/tree/d083b75b79386e95a3490a75b1498ad0958d9da8)
is not proof of the dataset's producing revision; its boundary modes/angles are
not Cartesian coil coordinates. Preserve error flags, nulls and incomplete
outcomes; record selection and expensive-verification policy.

Proposed split: group connected seed/target/trajectory descendants and
symmetry-equivalent geometry before assigning families. Join beta variants by
`misc.source_plasma_config_id`; group shared omnigenous target IDs and generation
lineage conservatively. Keep both matched arms and public descendants together.
QUASR ancestry and geometric duplicate checks remain prerequisites; row IDs,
random row splits and HF's `train` name do not establish a held-out family set.

Cheapest next decision: qualify a small licensed, provenance-bound set with
compatible target/coil labels and inspect lineage before freezing a split or
training. [Separate CoilStellaration documentation](https://github.com/proximafusion/coilstellaration/blob/03d1dc236044b97c5bd2fdf608a151754f9479dd/README.md)
advertises coil/requirement joins; its artifacts, rights and metric equivalence
are unqualified here. Missing labels in this inventory do not imply absent
community coil data. Additional native samples need a demonstrated coverage gap;
neither software checks nor this inventory imply physical acceptance.
