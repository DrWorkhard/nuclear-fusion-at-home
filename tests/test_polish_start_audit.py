import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_polish_start import verify_arrays


@pytest.mark.parametrize("bad", [np.zeros(206), np.full(207, np.nan), np.full(207, np.inf)])
def test_incomplete_nonfinite_qualification_arrays_rejected_before_reconstruction(bad):
    with pytest.raises(ValueError, match="complete finite"):
        verify_arrays({"x": bad}, {}, {}, {})
