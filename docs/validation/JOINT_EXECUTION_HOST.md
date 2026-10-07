# Temporary sleep prevention for a future joint comparison

The first [joint attempt](../optimization/ISSUE37_JOINT_RESULT.md) remains
inconclusive after host clock disagreement. The next operational decision is
whether temporary process-bound sleep assertions are usable on this Mac before
a separately registered comparison. A 7 October 2026 check supports that narrow
condition; it does not establish future uninterrupted execution.

On AC, the installed `caffeinate -i -s` exposed both idle-system and system-sleep
assertions before and after a 60.364811 s observation. Sixty samples showed a
maximum wall/monotonic difference of **0.001520822 s**. Explicit termination,
timed expiry and watched-process exit each removed owned assertions. All four
children were reaped. Total elapsed was 62.653091 s monotonic / 62.651510 s wall,
below the 120 s operational cap. No permanent power setting changed and no
scientific computation ran.

The exact external probe is identified by SHA256
`b5c7434c85ae46c67151349eff48059e5e8952929a109f5e07da669971fce410`.
It was not committed before execution; repository context
`c1dfbd8ce49152ed17d727b5b0aaf48478b0f08e` is not its producer revision.
The local archive below retains its source, original result, hashes, command,
installed executable/manual identities and read-only agent review. It is not
external peer review. Original local outputs remain intact.

AC was checked initially and assertions at observation endpoints, not
continuously. This did not test lid closure, forced sleep, host load or long-run
stability. The probe sets its completion flag before final cleanup/reporting
and lacks a guard after its last hash audit; final elapsed and reaped children
support the reported observation, but the script is not a scientific watchdog.

A future comparison still requires reviewed execution ownership/cleanup and its
own preregistration. Retain the original clock gate, budgets and failed record;
run fresh control and joint arms without free reuse of earlier work. The
actual-coil benefit endpoint remains unresolved.

Evidence: local-only tag `evidence-issue37-host-assertion-v1` (publication pending),
archive `9d8ab245e4c405f7e2af47d7ada14fb73b3d704a`,
files `evidence/issue37-host-assertion-v1/{README.md,probe.py,result.json,review.json,manifest.json}`.
The archive explains hash verification and how to repeat the bounded operational
observation using installed macOS tools and Python without package installation.
Repeating it produces new host observations, not a replay of historical timing.
