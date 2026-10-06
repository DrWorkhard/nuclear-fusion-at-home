"""Display the saved mid-radius sections; exploratory, without retracing or fitting."""
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

PAYLOAD = Path(__file__).resolve().parent
fig, axes = plt.subplots(2, 4, figsize=(12, 6.6), sharex=True, sharey=True)
phase_names = ('0', 'pi/2', 'pi', '3pi/2')
colors = ('#2466a3', '#d6771a')
for row, target in enumerate(('reference401', 'selected401')):
    report = json.loads((PAYLOAD/target/'run/result.json').read_text(encoding='utf-8'))
    with np.load(PAYLOAD/target/'run/control-contours.npz', allow_pickle=False) as data:
        target_rz = data['s0.5'].copy()
    target_rz = np.vstack((target_rz, target_rz[0]))
    for col, index in enumerate(range(8, 12)):
        ax = axes[row, col]
        line = report['lines'][index]
        with np.load(PAYLOAD/target/f'run/line-{index}.npz', allow_pickle=False) as data:
            hits = data['hits'].copy()
        hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
        hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
        for plane in (0, 1):
            points = hits[hits[:, 1] == plane]
            ax.scatter(np.hypot(points[:, 2], points[:, 3]), points[:, 4], s=3,
                       color=colors[plane], alpha=.7, linewidths=0,
                       label=f'phi = {"0" if plane == 0 else "pi"}')
        ax.plot(target_rz[:, 0], target_rz[:, 1], color='.6', linewidth=.6,
                linestyle='--', label='nominal target contour')
        ax.scatter(*report['center_RZ'], marker='+', color='.3', s=24, linewidths=.8)
        ax.set_title(f'{target}, theta = {phase_names[col]}\n'
                     +('qualified' if line['passed'] else 'unqualified'),
                     fontsize=9, color='#20354a' if line['passed'] else '#a52b2b')
        ax.set_aspect('equal', adjustable='box')
        ax.grid(alpha=.15)
        if row == 1:
            ax.set_xlabel('R [m]')
        if col == 0:
            ax.set_ylabel('Z [m]')
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncols=3, frameon=False, fontsize=9)
fig.suptitle('Nominal s = 0.50: saved section crossings, first 640 pooled hits\n'
             'Geometric launch phases; observations do not prove nested surfaces', fontsize=12)
fig.tight_layout(rect=(0, .06, 1, .91))
fig.savefig(PAYLOAD/'midradius-sections.png', dpi=160)
plt.close(fig)
