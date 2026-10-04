# Headroom continuation with a passing interior component

An exploratory six-coil geometry from 327 more L-BFGS-B iterations, started at the
[length-headroom candidate](../length-headroom-six-coil/README.md). It trades a 2.6%
higher boundary error for a 5.8× lower interior error, with scoped geometry intact.
**Both boundary limits still fail. This is not an accepted design.**

## Results (all checks on public inputs; evaluator revision `dc75fb3`)

| Check | Headroom start | This geometry | Limit |
| --- | ---: | ---: | ---: |
| Dense boundary normal RMS (64×64, one period) | 0.0019963 | 0.0020485 | 1e-4, fails |
| Dense boundary maximum normal error | 0.009426 | 0.009412 | 1e-3, fails |
| Interior vector RMS (ninner 64, 12,288 points) | 0.011479 | **0.0019880** | 0.01, **passes** |
| Coil–coil clearance lower bound | 0.06832 m | 0.06800 m | ≥0.06 m |
| Coil–plasma clearance lower bound | 0.13308 m | 0.13441 m | ≥0.08 m |
| Maximum sampled length / curvature | 3.4400 m / 10.04 | 3.4400 m / 10.02 | 3.5 m / 12 |
| Flux-normalized current | 308,140.6 A | 305,178.2 A | — |
| Public `sampled_normal_rms` (fixed current) | 0.0017440 | 0.0017899 | — |
| Public `sampled_inner_vector_rms` (fixed current) | 0.0361032 | 0.0341080 | — |

Public evaluation and replay (Python 3.14.8, macOS) give `report_replay_pass: true` and
`physical_admission: false`. The public sampled scores move in opposite directions:
- normal +2.6%, the same trade as the dense boundary;
- interior only −5.5%, because the public case freezes the current (see #9).

## How the dense and interior numbers were obtained

- **Boundary and current:** the dense boundary values and the current come from the `public dense-boundary` diagnostic proposed in #7.
- **Interior target:** regenerated from the committed `evidence/plasma-design-v2/reference-input-401.json` with vmecpp 0.8.0, then loaded with the unchanged `fusion_baselines.coupled_coils.load_target`. The regenerated target matches the starter's 64 shipped samples to 3.4e-10. It reproduces the headroom candidate's native interior RMS 0.01147939 exactly (see #10).
- **Geometry:** from the unchanged `clear_coil_geometry_audit.distance_certificate`, with ncoil 1024 and a 512×512 full-torus surface. Run on the start point, it reproduces the recorded headroom bounds: coil exact, plasma to 9e-16.

## Reproduce

The candidate remains usable by the current public evaluator. Its completed
construction driver and dependencies are preserved at commit **`bf51e3a`**; run
the commands below in a separate checkout of that revision. See
[historical reproduction](../../docs/validation/REPRODUCING_RESULTS.md).

Python 3.12 with `numpy scipy netCDF4 simsopt==1.11.1 vmecpp==0.8.0`, and one thread
(`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`):

```bash
python -c "import vmecpp; r = vmecpp.run(vmecpp.VmecInput.from_file('evidence/plasma-design-v2/reference-input-401.json'), max_threads=1); r.wout.save('results/wout_reference_regen.nc')"
python submissions/interior-pass-headroom-continuation/continue_fit.py results/wout_reference_regen.nc results/continuation 12 327 100000
```

The VMEC solve takes about 6 minutes and the 327 iterations about 10 minutes.

Construction details:
- `CoupledCoils` method "V" (boundary objective plus a 0.05-weighted interior term), with the headroom study's 3.44 m length penalty;
- ncoil 512, 64×64 boundary, ninner 32;
- a ±0.02 m box around the start, which no coefficient reached.

On the producing machine, a repeat run reproduced the final objective bit for bit (J = 1.6502969092034605e-6). Other platforms or library versions may differ at rounding level; compare the table, not hashes.

## Limits

- **Not the native search's model.** The construction is a simplified stand-in for the headroom study's model, whose seed chain depends on unpublished artifacts. The selection here was not preregistered for this trade. The run's own preregistered rule (lowest boundary RMS) would have kept the start.
- **Not converged.** The run stopped at its iteration cap while still descending (max gradient 1.3e-5).
- **Sampled geometry only.** Length and curvature are sampled maxima, not continuous upper bounds. No interval proof or finite-build model.
- **Scope.** One start, one machine. No realized magnetic surfaces, QI quality, Step 3 benefit transfer or engineering assessment.

## Attribution

Candidate data follow the starter's CC BY 4.0 attribution. Credit Goodman et al.'s
plasma data as in the [data provenance](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution).
Equilibrium regeneration used vmecpp (Proxima Fusion, MIT); coil construction used SIMSOPT.
No endorsement or affiliation is implied. Prepared by an AI agent; this is not external review.
