# Coil-freedom probe: move to joint optimization

Recorded 7 October 2026. [Issue #53](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53)
asked whether six order-8 coils should replace the order-5 family. Both arms
completed, but the probe reduced boundary RMS by **3.78%**, missing the registered
**50%** hurdle. The declared research-allocation rule selects **joint plasma/coil
optimization next**. No accepted design or physical benefit follows.

## Frozen comparison and result

Clean producer/evaluator `fd99245147308b9dbd23473002968e3283bd08fe` contains the
[prospective protocol](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/fd99245147308b9dbd23473002968e3283bd08fe/docs/optimization/ISSUE53_COIL_FREEDOM.md).
The reviewed fitter fix preceded execution. C then P used the identical original
length-headroom seed and reference401 Wout; P added only zero modes 6–8.
Current-normalization, flux and target B² conventions and acceptance limits stayed
fixed; selected currents were frozen for diagnostics. Each search
received 1800 s including intake/startup, then at most 900 s shared diagnostics,
one native thread and 256 MiB retained output. Both stopped at the search deadline;
late trials were excluded. No search was extended or repeated.

| Diagnostic | C: order 5 | P: order 8 |
| --- | ---: | ---: |
| Fine boundary RMS, maximum of two shifts | 0.00183501529 | 0.00176571369 |
| Fine maximum normal error | 0.00844233727 | 0.00827467258 |
| Finest interior vector RMS | 0.0101035400 | 0.00948113791 |
| Continuous geometry checks | Pass | Pass |
| Current, A | 307796.43 | 307603.43 |
| Direct lines completing 200 turns | 10/10 | 10/10 |
| Maximum signed-iota mismatch | 0.00629386 | 0.00584157 |
| Total monotonic seconds, including diagnostics | 2046.71 | 2078.83 |

P/C boundary RMS is **0.9622337751**, above the required 0.5. Geometry passes and
interior error improves; P alone passes the 0.01 interior limit. Both still fail
boundary RMS 1e-4 and maximum error 1e-3. Length upper bounds are 3.47012 / 3.46487 m
against 3.5 m; coil-clearance lower bounds 0.060715 / 0.064766 m against 0.06 m.
Full geometry, current, per-line and resource records remain in the archive.

## Limits and reproduction

Budgets were enforced using **monotonic time**. Fit-to-trace wall timestamps span
10239 / 5039 s, versus 1806 / 1819 monotonic seconds for fitting and its checks.
The cause is unknown; suspension or clock adjustment is possible. External host
load could not be verified. This is not controlled wall-time throughput or proof
of a plateau's cause, a global optimum or the coil family's ultimate capability.
Target-labelled traces do not establish nested surfaces, equal realized flux
labels or benefit transfer. [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md) remain open.

Full evidence is in local annotated tag `evidence-issue53-coil-freedom-v1`, archive
`293d0a65601c8293c936617f720fcfe099b3a27f`, tag object
`a76dc5d124203a4556d9a5f6eecc96c129bc1d03`; **publication is pending**. Its README,
manifest, summary and replay preserve all trials, original seed, diagnostic arrays,
traces, source identities and timing limitations. Original Wout remains local;
replay of saved field metrics and sampled independent/native B/A needs only
NumPy/SciPy. It does not rerun geometry or tracing. Original raw output remains at
`artifacts/issue53-coil-freedom-v1/`. Agent review is not external physics review.
