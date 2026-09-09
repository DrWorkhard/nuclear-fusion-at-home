#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
archive="${FUSION_QI_ARCHIVE:-$project_root/external/data/qifiles.zip}"
extract_root="$project_root/external/data/qifiles-v1"
download_url="https://zenodo.org/records/7220257/files/qifiles.zip?download=1"
expected_md5="f6983a41403da28247025be631522caa"

if [[ -n "${FUSION_QI_ARCHIVE:-}" && ! -f "$archive" ]]; then
  echo "ERROR: explicitly supplied QI archive does not exist: $archive" >&2
  exit 1
fi
mkdir -p "$project_root/external/data" "$extract_root"
if [[ ! -f "$archive" ]]; then
  curl --fail --location --continue-at - --output "$archive" "$download_url"
fi

if command -v md5 >/dev/null 2>&1; then
  actual_md5="$(md5 -q "$archive")"
else
  actual_md5="$(md5sum "$archive" | awk '{print $1}')"
fi

if [[ "$actual_md5" != "$expected_md5" ]]; then
  echo "ERROR: QI archive MD5 mismatch: expected $expected_md5, got $actual_md5" >&2
  exit 1
fi

unzip -t "$archive" >/dev/null
unzip -o "$archive" \
  'Files/configurations/nfp?/vacuum/input.QI_nfp?' \
  'Files/configurations/nfp?/vacuum/wout_QI_nfp?.nc' \
  'Files/optimization_files/Helpers.py' \
  'Files/optimization_files/Targets.py' \
  'Files/plots/plot_elephants/PltElephants.py' \
  'Files/plots/plot_boundaries/boozmn_QI_nfp?.nc' \
  'Files/plots/plot_epseffs_losses_vacc/PltEpsEffs_Losses_Vacc.py' \
  'Files/plots/plot_epseffs_losses_vacc/nfp?_eps_effs/ee_nfp?_beta0' \
  'Files/plots/plot_epseffs_losses_vacc/nfp?_particle_data_s=0.25/confined_fraction.dat' \
  -d "$extract_root" >/dev/null

uv run --locked fusion-baselines validate-manifest \
  "$project_root/manifests/qi-goodman-2022.json" \
  --data-root "$project_root"
echo "verified: Goodman et al. QI data release v1.0"
