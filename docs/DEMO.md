# Demo

A real terminal session, captured by `scripts/make_demo.sh` on 2026-11-20
(3.13.18 on Linux).
Nothing here needs a key or the network. Models named `fake:...` are simulators.

## Version

```console
$ .venv/bin/calibra --version
calibra-eval 0.1.0rc1
```

## Replay the judge calibration suite from fixtures

```console
$ .venv/bin/calibra run --out /tmp/demo examples/judge_calibration/suite.toml
== judge_calibration (seed 1, recorded 2026-11-20, replay mode)
Measure                                                  Value (95% CI)                   
-------------------------------------------------------  ---------------------------------
Cases with ground truth                                  72                               
Percent agreement                                        0.764 [0.667, 0.848]             
Cohen's kappa                                            0.528 [0.337, 0.698]             
Judge errors                                             17 of 72                         
Unreadable verdicts (scored against the judge)           0                                
Position: same pick after swap                           0.500 [0.333, 0.667]             
Position: picks answer A                                 0.667 [0.556, 0.778]             
Position: accuracy gap, right answer first minus second  +0.333 [0.127, 0.540] (normal CI)
Verbosity: accepts wrong answers, raw                    0.333 [0.194, 0.500]             
Verbosity: accepts wrong answers, padded                 0.639 [0.472, 0.778]             
Verbosity: padded minus raw, wrong answers               +0.306 [0.134, 0.477] (normal CI)

wrote /tmp/demo/judge_calibration.json
```

## Replay the code suite and compare two models with paired statistics

```console
$ .venv/bin/calibra run --out /tmp/demo examples/code_tasks/suite.toml
== code_tasks (seed 1, recorded 2026-11-20, replay mode)
Target  Model                     Pass rate (95% CI)    pass@1 (95% CI)       pass@5 (95% CI)     
------  ------------------------  --------------------  --------------------  --------------------
strong  fake:coder-strong (fake)  0.900 [0.800, 0.975]  0.900 [0.800, 0.975]  1.000 [1.000, 1.000]
weak    fake:coder-weak (fake)    0.575 [0.412, 0.725]  0.575 [0.412, 0.725]  0.875 [0.688, 1.000]
paired strong - weak: +0.325 CI [0.202, 0.448] (unpaired CI [0.143, 0.507])

wrote /tmp/demo/code_tasks.json
```

## Replay is byte-identical

```console
$ bash scripts/replay_twice.sh
identical across runs: code_tasks.json (f913fe223dee09fc)
matches committed results/code_tasks.json
identical across runs: json_extract.json (728cbddf6e1d673b)
matches committed results/json_extract.json
identical across runs: judge_calibration.json (7f03d5ef939d0693)
matches committed results/judge_calibration.json
```

## The README tables match the result files

```console
$ .venv/bin/calibra readme --check
README matches the result files
```

## A missing fixture fails loudly in replay mode

```console
$ cp -r examples/json_extract /tmp/demo/je && : > /tmp/demo/je/fixtures.jsonl && (.venv/bin/calibra run --out /tmp/demo /tmp/demo/je/suite.toml 2>&1 | tail -1) || true
error: replay mode: no fixture for request key 166cfe980c004ec2f2d4e8137138b709f7fff5db2795758043b2d6c7ce5983cf. Run with --record to create it.
```

