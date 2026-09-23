# Portable public layer: verification record

23September2026. The [release specification](PUBLIC_RELEASE.md) fixes the scope
and numerical checks. This report records implementation outcomes separately.
No new optimization or change to historical scientific acceptance is claimed.

## Software qualification

36 standard-library public unit/analytic tests pass, with final repeat in0.266s. The initial35-test
run exposed a JSON-depth assumption; explicit depth/node limits corrected it.
Tests cover analytic circle fields, SI derivatives, current sign/linearity,
translation, physical-copy mapping, candidate/data/report tampering, file
preservation and optional cost/unrequested-topic metadata.

The first full historical regression had2061passes/3failures/334known warnings
in210.51s: frozen CI had been edited. That file was restored byte-for-byte and
the new CI added separately. No preservation exception or physical threshold was
changed.93 focused old controls then pass in7.65s; the corrected full suite has
2064passes,334known warnings, zero failures/errors/skips in213.23s. Both runs
and final source/data digests are retained in the
[software qualification](../../evidence/public-layer-v1-software.json).

Ruff, documentation and whitespace checks pass. Static checks verify read-only
public-CI permissions, pinned actions, no privileged trigger, no secrets and
nonpersisted checkout credentials. Hosted Linux/macOS/Windows execution has not
been observed. A limited secret-pattern scan of new files finds no matches;
whole-history rights/privacy/security review remains outstanding.

## Portable data

Three JSON files total116,178bytes. Parent audit/run/bundle/snapshot/array/
equilibrium hashes are bound during the read-only derivative export. Original
private paths are not copied into the packet; old files remain unchanged.
Zenodo's official record API confirms the original dataset's creator, version,
CC-BY-4.0 license and the archive checksum already in our manifest. No large
archive was fetched. [Attribution and conventions](../../examples/clear-coil-samples-v1/README.md).

## Real copied-tree qualification

Pending execution from the committed software version. Planned: empty fresh
output, only public files copied, no Git/native environment/history/artifacts,
site packages disabled, Python socket audit guard, then reference/native-value
comparison, same-evaluator replay, one fixed1micrometre candidate change and
replay, forged-admission/overwrite rejection, optional-cost metadata check.

This is a portability/arithmetic/interface check, not an optimization study,
independent-hardware reproduction, OS sandbox proof or physical design admission.
No hosted bot, publication or automatic merge is enabled by these changes.
