# Manufacturing-robustness protocol

## Purpose

This protocol measures how strongly a serialized filamentary coil solution loses
normal-field accuracy under spatially correlated geometric manufacturing errors.
It is a screening metric, not a complete winding-pack or assembly-tolerance model.
The distribution and acceptance rule are frozen before comparing optimizers.

## Frozen distribution (version 1)

- Perturbation family: zero-mean Gaussian process applied independently to every
  physical coil copy, using StellCoilBench/SIMSOPT's `GaussianSampler` and
  `CurvePerturbed` implementation.
- Kernel: squared exponential in coil arclength.
- Reactor-scale correlation length: `1.0 m`.
- Reactor-scale standard-deviation search interval: `0.0001–0.05 m`.
- Monte Carlo draws per amplitude: `100` for baseline screening.
- Random generator and seed: NumPy `PCG64DXSM`, common base seed `20260830`.
- Acceptance rule: the 95th percentile of
  `squared_flux(perturbed) / squared_flux(nominal)` is at most `2.0`.
- Reported statistic: the largest accepted standard deviation `sigma*`, in
  reactor-scale millimetres.

The benchmark coils are stored in device coordinates. Length-like perturbation
parameters are therefore divided by the case's recorded ARIES-CS length scale
before evaluation and `sigma*` is multiplied by the same factor for reporting.
The nominal squared-flux threshold is read from the exact case file.

## Required numerical checks

1. Both endpoints are evaluated with the same random draws used by bisection.
2. The lower endpoint must pass and the upper endpoint must fail; otherwise the
   value is reported as unbracketed rather than as a measured `sigma*`.
3. Bisection uses common random numbers at every amplitude and stops only after
   the relative bracket width is below 5% or after 20 iterations.
4. An accepted comparative result must later be repeated with at least 1,000
   draws, additional seeds, and a distinct holdout sample set.

## Interpretation limits

This metric probes centerline errors and normal-field degradation only. It does
not include correlated metrology/assembly modes, conductor strain, winding-pack
cross-section, elastic response, current errors, thermal contraction, or
free-boundary plasma response. It may reject a candidate, but cannot by itself
certify a buildable coil system.
