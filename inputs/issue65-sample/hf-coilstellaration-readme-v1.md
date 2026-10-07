---
configs:
- config_name: results
  default: true
  data_files:
  - split: train
    path: results/train-part-*.parquet
  - split: eval
    path: results/eval-part-*.parquet
- config_name: metrics
  data_files: metrics/part-*.parquet
- config_name: requirements
  data_files: requirements/part-*.parquet
- config_name: coilsets
  data_files: coilsets/part-*.parquet
license: mit
language:
- en
tags:
- coilsets
- stellarators
- fusion
- optimization
- engineering
pretty_name: CoilStellaration
size_categories:
- 1M<n<10M
---