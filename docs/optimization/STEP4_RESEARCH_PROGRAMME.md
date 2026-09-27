# Near-term research programme

Updated 27 September 2026. [Status](../STATUS.md) · [Step 4](../steps/STEP_4_PLASMA_AND_COILS.md)

## Focus

Use the method that moves field error: penalized normalized coil fitting.
The headroom fit reaches **0.001996 with scoped geometry checks**. Longer coils
reach 0.001948 and pass the interior-vector component, but length bounds are
unresolved. The unchanged boundary acceptance limit remains 1e-4.
Failed starts and interrupted runs remain evidence, not erased from effort.

## Next work

The [longer-fit comparison](LONGER_COIL_EXPLORATION.md) shows enough progress to
continue fitting, with explicit attention to construction headroom.

1. Investigate objective scaling/stopping and penalty conditioning: the expanded
   headroom fit has no active box bounds, but stops on objective change well
   before its gradient tolerance. This is not proof of an optimum. Retain length
   margin and leave acceptance unchanged. Map field error against clearance, curvature,
   current and coil complexity. Consider the existing eight-coil family as a
   separately labelled comparison if the present family stalls.
2. Freeze the best two or three candidates, then use the shared trusted field
   and continuous-geometry checks. Investigate realized-field topology and
   matched realization of the Step 3 target before claiming benefit transfer.

Exploration needs one short record: script/input/output identities, question,
wall-clock/resource ceiling and conclusion. Do not add arbitrary evaluation or
coefficient caps; retain them when needed for a particular matched experiment.
Past studies retain their original rules. No routine full historical regression,
new orchestration framework or separately written checker for every script.

By **24 October 2026**, review the reachability/trade-off map. The 1e-2 signal now
supports further local fitting; it does not promise success. If progress stalls,
change family/target rather than automatically extend a failed method.

## MS0 and community value

Target **26 March 2027**: a useful attributed open coil challenge with calibrated
gate interpretation, positive/negative controls and separate-machine reproduction.
First assess contributing the Goodman case and checked coils to an existing
benchmark such as StellCoilBench. Build only missing adapters, not a parallel
benchmark platform by default.

Near-term contributions: metric crosswalks, portable target/coil exports,
independent checks and replications. Unsolicited approaches remain welcome.
Hosting, publication, external contact and a backup destination still require
the owner's authority. No such external action has occurred.

Pressure, engineering and SQuID-C work are parked until an actual coil set is
within ten times the field-error limit, unless evidence justifies revisiting them.
They remain required for eventual completion; detailed historical plans are at
the [freeze tag](../validation/REPRODUCING_RESULTS.md). Proxima contact waits for MS1.
