# Level 2: for a teenager

Updated 6 October 2026 · [All five levels](README.md) ·
Previous: [Level 1](LEVEL_1_CHILD.md) · Next: [Level 3](LEVEL_3_UNIVERSITY.md)

## Fusion in one paragraph

Fusion joins light atomic nuclei into heavier ones. Power plants would most likely
fuse two kinds of hydrogen, deuterium and tritium, into helium. A tiny amount of
mass disappears and becomes a lot of energy (E = mc²). The Sun manages this with
its enormous gravity. On Earth the fuel must be heated to over 100 million °C.
At that temperature it is a **plasma**: a gas of electrically charged particles.
No wall can touch it, but charged particles spiral along magnetic field lines, so
magnets can hold it away from the walls.

## Two kinds of magnetic bottle

Bend magnetic field lines into a ring (a doughnut, or torus) and the plasma still
drifts outwards. Twisting the field lines as they go around fixes most of that.

- A **tokamak** twists the field by driving a huge electric current through the
  plasma itself. ITER, being built in France, is a tokamak.
- A **stellarator** twists the field with the 3D shape of its external magnet
  coils. Wendelstein 7-X in Germany is the largest one.

Stellarators can run continuously and need no large current inside the plasma,
which avoids some sudden plasma failures. The price is complicated 3D coils, so
designing one is a hard computer problem. That is why we work on stellarators:
their design can be explored largely on computers.

## Our two-part puzzle

1. **Plasma shape:** which twisted doughnut keeps the particles in best?
2. **Coils:** which set of wiggly coils creates exactly that magnetic field while
   staying buildable: not too long, not too sharply bent, and not too close to
   each other or to the plasma?

Anyone can contribute through GitHub, usually by asking an AI agent to do a piece
of the work. Every result is checked separately from the way it was produced, and
failures are kept, not hidden.

## Where we are (October 2026)

- **Steps 1–3 are done, in a small scope.** We can reproduce known results, repeat
  a design cycle reliably, and we improved a plasma shape by 5–11% on one specific
  computer test of particle confinement.
- **Step 4 is in progress: coils.** Our best coil set satisfies the shape rules,
  but its field leaks through the plasma boundary about **19 times** more than our
  limit, and the field inside is about 7% further off than allowed. Its field
  lines stay inside and twist by about the right amount, which is encouraging but
  not proof.
- We have now fitted coils, with equal effort, to both the original and our
  improved plasma shape. Both miss the limits by similar amounts. Our particle
  test could only be finished in a narrow region, where the improved shape is
  still about 5% better. In the wider region the coil fields lack some of the
  magnetic dips the test needs, so we cannot yet say whether the improvement
  survives with real coils.
- **Our current method has stalled.** Thirty more minutes of computer search
  improved the coils by only 6%, and we needed a factor of two to keep going. We
  accept that and change course: one quick test with more flexible coil shapes
  decides, by 24 October 2026, whether to use more flexible coils or to design the
  plasma shape and the coils together.
- **Step 5 and a working reactor design are not reached.** The 2030 goal is an
  ambition to aim for, not a promise.

## Try it

With Python 3.11 or newer, the [guide](../../README_agents.md#start-in-three-commands)
shows three commands that run on an ordinary laptop. You can change one number of
a coil's shape and see whether the errors go down.
