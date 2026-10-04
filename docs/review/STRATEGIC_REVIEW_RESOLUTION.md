# Assessment against the README vision

4 October 2026. Internal assessment, not external peer review.
[Evidence](../STATUS.md) · [Plan](../PROJECT_PLAN.md)

**Current results do not support the README's reactor-design timeline.** The
project can make a useful contribution by answering one consequential design
question and making that answer reproducible.

Three changes matter:

1. **Test the actual benefit.** Current coil fits target reference401, not the
   improved Step 3 plasma. Boundary error alone does not establish magnetic
   surfaces, confinement or transfer of the vacuum diagnostic gain.
2. **Stop extending a recipe without a decision.** Diagnose conditioning once;
   compare actual fields under matched conditions. If progress stalls, change
   family/target or compare joint plasma/coil optimization in existing software.
   [Jorge et al.](https://arxiv.org/abs/2302.10622) demonstrate the latter approach;
   that does not establish success on our case.
3. **Screen reactor relevance early.** Expose assumptions about power balance,
   pressure, magnets, blanket/shield space, heat exhaust and maintenance before
   expensive optimization. [Stellaris's integrated concept](https://www.proximafusion.com/press-news/proxima-fusion-and-partners-publish-stellaris-fusion-power-plant-concept-to-bring-limitless-safe-clean-energy-to-the-grid)
   illustrates that broader scope; it is not our matched comparator or proof of
   buildability. A vacuum diagnostic cannot substantiate power-plant performance.

The [programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) sets the October decision.
Make the decisive target/checker portable before building more infrastructure.
Keep active fitting and shared acceptance code; remove completed drivers and
repeat summaries. Original evidence and raw data remain intact; methods and
failure details resolve at their [historical revisions](../validation/REPRODUCING_RESULTS.md).
The root README and acceptance limits remain unchanged. No new physical result
is claimed.
