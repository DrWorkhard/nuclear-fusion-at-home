"""Capture one seeded row's effective VMEC settings before returning them to the solver.

The future native launcher supplies the already imported settings module. This
helper imports no scientific packages and does not authorize or launch a solve.
Adapted from the recorded #112 radial wrapper's capture_defaults context manager.
"""

import json
from contextlib import contextmanager


def canonical(value):
    """Compare every field and JSON type, rejecting nonfinite values."""
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


@contextmanager
def capture_row_settings(module, output, row, expected):
    """Require exactly one unchanged preset per scorer invocation; always restore."""
    original = module.create_vmec_settings_from_preset
    frozen = canonical(expected)
    recorded = []

    def create(boundary, settings):
        if recorded:
            raise ValueError("multiple effective settings objects for one seeded row")
        if (settings.fidelity != "high_fidelity" or settings.multithreaded is not False
                or settings.verbose is not False):
            raise ValueError("unchanged default preset required")
        model = original(boundary, settings=settings)
        data = model.model_dump(mode="json")
        # Retain unexpected settings before rejecting them; never return them to VMEC.
        with (output / f"{row['target_id']}-effective-settings.json").open(
                "x", encoding="utf-8") as stream:
            json.dump(dict(global_row=row["global_row"], target_id=row["target_id"],
                           effective_vmec_settings=data), stream, indent=2, allow_nan=False)
            stream.write("\n")
        recorded.append(data)
        if canonical(data) != frozen:
            raise ValueError("effective VMEC settings differ from frozen protocol")
        return model

    module.create_vmec_settings_from_preset = create
    try:
        yield recorded
        if len(recorded) != 1:
            raise ValueError("one effective settings object required for seeded row")
    finally:
        module.create_vmec_settings_from_preset = original
