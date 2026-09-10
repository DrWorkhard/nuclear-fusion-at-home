# Rejected LPQA warm-start fixture

This is our locally generated order-4 LPQA v1.1 L-BFGS-B screening candidate,
**not** an authoritative Proxima/SQuID-C design and **not** an accepted physical
baseline. It fails the 1e-8 quadratic-flux cut-in. We preserve it solely as an
immutable input for reproducible numerical experiments and regression tests.

- Original generated field SHA-256:
  `7ae1b1968b8ca34fa94cc0e67cfad41577219ed43bcd902b695c7b7cc04ecd2e`.
- Tracked field.json SHA-256:
  `ef38a96aa6820de08d187f6362645b5450f009034706b06b2722566da9631e8c`.
- The only byte change is one added terminal LF. Removing exactly that byte
  recovers the original hash; no numeric value or serialization reference changed.
- The SIMSOPT serialization includes +/-Infinity for unbounded optimizer DOF
  bounds. This is the producer's Python-compatible JSON convention, not strict
  RFC JSON; do not silently convert those values or use them as physical data.
- Producer input: cases/lpqa_engineering_v1p1_lbfgsb.yaml, SHA-256
  `4a0bd130270fc887988ac33de974e04b6fac6da2da2faaa0e66a4f49535b64b9`.
- LPQA target: pinned StellCoilBench input.LandremanPaul2021_QA, SHA-256
  `4c6ba4bc391a69b5b6a5e84ff82df9b0ce92e20c42f2a47f89a9283fd5bc3458`.

producer_provenance.json preserves the historical record verbatim apart from
text-file newline handling. It reports exact external code pins but **no project
commit and a dirty project tree**. Thus the original run is not retrospectively
claimed to have a fully versioned producer. This snapshot freezes the starting
data now; later experiments have their own committed evaluators and protocols.

The field is a project-generated output using the public Landreman–Paul target
distributed with the pinned StellCoilBench release. Source citations and code
licenses remain as documented in this repository; it must not be advertised as
author-supplied coil data. No external files need to be fetched to obtain this
particular starting coil state after cloning the repository.
