# Dynamic Traffic Testing

## Project overview and purpose

A YAML-driven RF long-stability / dynamic-traffic test toolkit. Clients describe power meters, BBU, iperf traffic profiles, and UE lock/call parameters in YAML; the runner schedules profiles, samples power, and stores verdicts.

`core/` is the offline-testable business layer (config validation, power thresholds, profile scheduling, SQLite results). `l3_ddtt_tool/` is the lab runtime. Optional site-specific BBU and UE backends are loaded through environment variables; see CONFIGURATION.md.

## Feature list

- YAML-driven configuration: power meter, BBU, iperf traffic profiles, UE lock/call parameters
- Abstract test executor plus factory pattern (`TestRunnerFactory` / `IperfTestRunner`)
- Multi-process iperf traffic and power-meter sampling, with child-process cleanup at the end
- SQLite result storage; power verdict **power > pMax + 3 dB**
- Alarm collection thread, UE cell lock and call-control adapters
- `core/` pure-logic layer + pytest unit tests + GitHub Actions CI
- Pure-Python `utilityLib` stand-in (original deployment may use a compiled extension), covering overshoot / overlap / frame slicing

## Tech stack and dependencies

- Python 3.9+
- Lab runtime: PyYAML, NumPy, pandas, PyVISA, Paramiko, openpyxl
- Unit tests: pytest, pytest-cov (no instruments)
- Lab optional: BBU admin API and UE control libraries, loaded via environment variables

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## How to run and use

1. Copy `examples/main_config.example.yaml` to a local `main_config.yaml` (do not commit real values).
2. Fill instrument / BBU / UE addresses and passwords via environment variables or a local untracked file.
3. From a working directory that contains `l3_ddtt_tool`, call `TestRunnerFactory` from Robot / Python.

Unit tests (no devices):

```bash
python -m pytest -v --cov=core --cov-report=term-missing
```

Syntax check:

```bash
python -m py_compile l3_ddtt_tool/*.py l3_ddtt_tool/utility/*.py core/*.py
```

## Project file structure

```text
.
├── README.md
├── CONFIGURATION.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .github/workflows/ci.yml
├── examples/main_config.example.yaml
├── core/                      # offline-testable business logic
│   ├── config.py              # YAML validation
│   ├── judgment.py            # pMax+3dB verdict
│   ├── profiles.py            # profile scheduling
│   ├── results_db.py          # SQLite results
│   └── ue_identity.py         # UE IP/PCI consistency
├── l3_ddtt_tool/              # lab runtime
└── tests/
```
