import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("script", ["bootstrap_macos.sh", "bootstrap_vmec2000.sh"])
def test_no_system_install_mode_fails_before_any_install(tmp_path, script):
    marker = tmp_path / "unexpected-install"
    fake = {
        "uv": "#!/bin/sh\nexit 0\n",
        "uname": '#!/bin/sh\nif [ "$1" = -s ]; then echo Darwin; else echo arm64; fi\n',
        "brew": '#!/bin/sh\nif [ "$1" = install ]; then touch "$FUSION_TEST_MARKER"; fi\nexit 1\n',
    }
    for name, text in fake.items():
        path = tmp_path / name
        path.write_text(text)
        path.chmod(0o755)
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "PATH": f"{tmp_path}:/usr/bin:/bin",
        "FUSION_NO_SYSTEM_INSTALL": "1",
        "FUSION_TEST_MARKER": str(marker),
    }
    result = subprocess.run(
        ["/bin/bash", str(root / "scripts" / script)], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "system installation forbidden" in result.stderr
    assert not marker.exists()
