# Dynamic Traffic Testing configuration

Put real values in a local untracked file or environment variables. Do not commit them.

| Variable / field | Meaning | Example |
|---|---|---|
| `POWER_SENSOR_IP1` | Power meter address | `127.0.0.1` |
| `BBU_IP` | BBU management address | `127.0.0.1` |
| `TRAFICC_PROFILE.SERVER_IP` | iperf server | `127.0.0.1` |
| `ue_su_passwd` / `password` / `root_password` | UE / server password | `${ENV_PASSWORD}` or `YOUR_SECRET` |
| `pMax` | Power verdict threshold (dBm) | `40` |
| `LAB_BBU_ADMIN_MODULE` | Optional module that exposes `admin` | unset uses in-repo stubs |
| `LAB_BBU_EXCEPTION_MODULE` | Optional module that exposes `AdminApiConnectionClosedException` | unset uses in-repo stubs |
| `LAB_UE_MODULE` | Optional module that exposes `PythonApi` | unset uses in-repo stubs |
| `ABSTRACT_LIB_CONFIG` | Path to the UE pool YAML used by the UE backend | local untracked file |

Copy `examples/main_config.example.yaml` and edit a local copy. Add that copy to `.gitignore`.

You can also put `LAB_*` values in a gitignored `.env` at the repo root. `l3_ddtt_tool/optional_lab.py` loads that file before importing backends.

Power FAIL matches the lab runtime: `power > pMax + 3` (see `core/judgment.py` and `l3_ddtt_tool/result.py`).
