# Assessment against the README vision

4 October 2026. Internal assessment, not external physics or engineering review.
[Status](../STATUS.md) · [Decisions and priorities](../PROJECT_PLAN.md)

**The current evidence does not support the README's year-end reactor-design
vision or a credible delivery schedule.** The project has useful numerical tools
and an open contribution route. It has not demonstrated a reactor advantage.
The fastest credible contribution is to resolve one consequential design question
and make its answer independently reproducible.

## What is holding progress back?

1. **The optimization target is disconnected from the claimed benefit.**
   All current coil fits use reference401, not the improved Step 3 target.
   Step 3 improved a vacuum bounce-action diagnostic; preservation in actual
   coil fields, confinement and finite-pressure performance remain untested.
   A better boundary fit alone cannot close that chain.
2. **Local progress is slowing.** The best geometry-checked normal RMS is
   0.001996, about 20 times its limit; interior RMS 0.01148 also fails.
   Expanding the latest box improved boundary RMS only 2.64%. The solver stopped
   above its gradient tolerance, so this is neither an optimum nor proof that
   the coil family cannot work. One conditioning comparison is justified;
   indefinite extensions of the same search are not.
3. **Reactor relevance is being considered too late.** Waiting for a boundary
   threshold before considering any pressure or engineering question can spend
   months optimizing an unsuitable target. Start cheap feasibility screens now;
   defer expensive simulations until they answer a specific decision.
4. **Contributors cannot reproduce the decisive test.** Public sparse evaluation
   and the newer dense boundary diagnostic help, but the full native interior
   data and acceptance path still depend on local artifacts. The immediate
   collaboration bottleneck is a portable target and checker, not a leaderboard
   or more orchestration.

## Scientific correction

Measure improvement in the **realized field under matched conditions**, alongside
coil geometry and current. Inspect magnetic surfaces and islands early, including
on failing candidates as diagnostics. Compare reference and improved targets with
matched fitting effort before calling Step 3 useful to coil design. Keep the
existing field and geometry limits; calibrate their physical relevance separately.

If the fixed-target family stalls, compare a different family or joint plasma/coil
optimization using existing tools. This is a supported alternative, not a promised
cure: [Jorge et al. (2023)](https://arxiv.org/abs/2302.10622) demonstrate simultaneous
optimization in vacuum and finite-pressure examples, not success on our case.

A reactor screen must expose assumptions about net electric power, confinement,
pressure, magnet loads, blanket/shield space, heat exhaust and maintenance.
[Proxima's Stellaris concept overview](https://www.proximafusion.com/press-news/proxima-fusion-and-partners-publish-stellaris-fusion-power-plant-concept-to-bring-limitless-safe-clean-energy-to-the-grid)
illustrates the breadth of integrated analysis; it is not a matched comparison
or proof that either design can be built tomorrow. Unknowns remain unknowns.
Our inference is that a single vacuum magnetic diagnostic cannot substantiate
power-plant performance.

## Keep the implementation small

Keep the public interface, normalized fitter, shared acceptance mathematics and
scientific evidence. Retire completed leaf drivers and their tests, unused package
extras and inactive environment manifests. Keep the fitter's imported **and
hash-bound** dependencies; deleting those would break replay. Exact historical
runs use their recorded revisions, not edited current code.

Replace old reviews and duplicated decision/lesson lists with this assessment,
the roadmap and current verification. History remains in Git. The root README,
acceptance code, evidence identities, raw outputs and installed native environments
are unchanged. [Reproduction](../validation/REPRODUCING_RESULTS.md).

The [programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) makes this assessment
an explicit continue/change/stop decision. No new physical result is claimed.
