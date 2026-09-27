# Candidate contributions

This directory is tracked by Git. Use a unique descriptive folder, for example
`submissions/my-coil-study/`, containing:

- `candidate.json`: the small public candidate (about 10 KB), with its original
  schema, case ID, units and named coefficients.
- `README.md`: your question/change, reference and trusted evaluator revision,
  exact reproduction commands, both scores, trade-offs, checks and limitations.
  Credit any reused work. Compute spending and agent/model details are optional.

Start from the bundled reference or inspect the
[constraint-aware shape example](constraint-aware-shape52/README.md): a saved
research geometry that improves both public sampled scores, with explicit
current differences and limits. It does not replace the reference benchmark.

Keep generated reports, audit JSON and raw runs in `results/` (intentionally
ignored); include their command outputs or a concise summary in the PR. Do not
force-add the large report when the candidate and commands reproduce it. If a
claim genuinely needs additional evidence, agree a size-appropriate artifact route.

After creating your candidate and summary:

```bash
git add submissions/my-coil-study/candidate.json submissions/my-coil-study/README.md
```

Review the staged diff before committing. This directory is not an automatic
submission queue or a claim of physical acceptance. Other methods, counterexamples
and negative results may use an appropriate focused code/docs PR instead.
[Contribution guide](../CONTRIBUTING.md) · [Quickstart](../docs/validation/PUBLIC_QUICKSTART.md)
