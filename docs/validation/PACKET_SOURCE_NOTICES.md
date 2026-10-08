# Portable packet source and attribution check

On 7 October 2026, a scoped check of the two portable data packets found two
broken historical-source links in [NOTICE](../../NOTICE.md). The linked archive
`68db098b664bb072854b687040e103aaafee463c` does not contain either referenced
metadata file. Both corrected links resolve to published pre-migration commit
`a32f30d57e45c8f9b869e0abdd98d4f547a49d75`; GitHub-returned bytes and Git blob IDs
match the local historical objects. No historical commit or tag was changed.

| Material reviewed | Source binding | Disposition |
| --- | --- | --- |
| `clear-coil-samples-v1` data | Existing packet manifest and parent digests; its README records the original export and native source | Retain its CC BY 4.0 creator, DOI, license and changes notice. No data changes. |
| `clear-coil-interior-v1` data | Manifest `9f9b32ffb6176b22e149069896500da0ac1aa0c371b5f17be7fa7603ebfb2ccb`; per-target input/Wout/NPZ hashes; original #25 archive `05a4511084912fea9bd8d03e81f01018882396b8` | Name both packets in NOTICE; add the direct CC BY 4.0 link and frozen upstream version/date to the dense README. No data changes. |
| Original project source/documentation | Root LICENSE and NOTICE | Preserve MIT code versus CC BY data distinction. Native dependency software and full upstream dataset are not bundled in the portable copy. |
| Historical license metadata | `references/public-data-sources.json` at `a32f30d`; blob `aeb4c9238f81d3264a8678da167216dc0f494d58` | Repair the source link; retain the original dated record. |
| Historical source identities | `references/external_sources.json` at `a32f30d`; blob `27b33d1ea3aa87680f8b76d20053a16454346297` | Repair the source link. Version identities alone do not establish redistribution rights. |

Fresh retrieval of the [Zenodo record API](https://zenodo.org/api/records/7220257)
matches the historical selected metadata: Alan Goodman, *Data for paper
“Constructing precisely quasi-isodynamic magnetic fields”*, version 1.0,
18 October 2022, DOI `10.5281/zenodo.7220257`, license ID `cc-by-4.0`.
The `qifiles.zip` record lists 1,057,077,931 bytes and MD5
`f6983a41403da28247025be631522caa`. The archive was not downloaded again or its
contents re-audited. The retrieved API response SHA-256 is
`7747fcaa705cd4e9babb163dc541246753abc1df03e610d8f4320a9d09e3a569`;
the original response remains in the local review bundle. Live API statistics
can change its full response hash without changing the selected metadata.

The [CC BY 4.0 notice](https://creativecommons.org/licenses/by/4.0/) calls for
credit, a license link and an indication of modifications, without implying
endorsement. The packet READMEs state the project's vacuum calculation, coil
construction/fitting, sampling and, for the dense packet, Step 3 boundary changes.
This review checks those notices and recorded source identities. It does not
independently reconstruct the entire upstream-to-project transformation history,
inspect every upstream archive member or clear other historical artifact families.
[Issue #2](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/2) and the
[full-history review](PUBLICATION_INVENTORY.md) remain open. No scientific result,
license grant, distribution-rights clearance or publication follows from this fix.

The two packet data manifests remain unchanged. The copied-release qualification
must carry the updated NOTICE and packet READMEs; numerical acceptance and native
environments remain unchanged. Agent review is not a legal review.
