# CHANGELOG

## 0.2.21

- [x] update: url param for enabling cors.

## 0.2.20

- [x] feat: serve on-cloud calls via fsm call audio api. s3 sync may take time so we make a request to serve via fsm.
    Since the scheme requires uuid, on-prem audios are not supported. Use `--on-prem` to prevent this from getting applied.

## 0.2.19

- [x] add: end date now takes 23:59:59 as max time inplace of 00:00:00.

## 0.2.18

- [x] add: offsets for start and end date along with start and end times (hour only).

## 0.2.17

- [x] fix: 'AttributeError: 'NoneType' object has no attribute 'get' on fetching calls with failed predictions.
- [x] update: Support python 3.8-3.10

## 0.2.16

- [x] perf: We retry a batch of turns if it fails due to any db error. Removed mandatory inter-batch delays.

## 0.2.15

- [x] fix: Optional state values are erroneous if not used via cli.

## 0.2.14

- [x] feat: We can filter data by states.

## 0.2.13

- [x] Fix: arg name `q_delay` fixed to `delay`.

## 0.2.12

- [x] Add: Delay flag on cli to increase connection timeout.
- [x] Update: Start and end dates are assumed to be current day's min and max timestamps.

## 0.2.11

- [x] Fix: Prediction being a `dict` breaks `sample` and `select` commands.
- [x] Update: JSON dumps retain utf8 chars.

## 0.2.10

- [x] Feat: Download calls dataset using call uuids from a given csv file.
- [x] Update: Prediction column added to calls dataset.

## 0.2.8

- [x] Add: Call history can be added to calls dataset by providing the `--history` flag.

## 0.2.7

- [x] Fix: Command `select` doesn't dispatch to select method.

## 0.2.6

- [x] Update: `sample` and `select` are sub-commands for skit-calls.
- [x] Feat: obtain calls directly by passing ids.
- [x] Fix: Turns are serialized to JSON strings if the value is `List` or `Dict`.

## 0.2.5

- [x] Fix: Separate call url and turn url parsing.

## 0.2.4

- [x] Fix: All urls are unquoted within the `Turns` model.

## 0.2.3

- [x] Update: progress bar and query updates.

## 0.2.2

- [x] Update: Downgrade pyyaml for integrations with other components.

## 0.2.1

- [x] Update: queries optimized.

## 0.2.0

- [x] Update: Move away from the api and use raw sql.
- [x] Perf: ~100k calls in 7 minutes. This is very slow but orders of magnitude faster than the previous of 10k calls in 10minutes.

## 0.1.6

- [x] Fix: Version read from package instead of toml.

## 0.1.5

- [x] Refactor: no noticable change on the cli.

## 0.1.4

- [x] Refactor: no noticable change on the cli.

## 0.1.3

- [x] Logger with increasing verbosity.
- [x] Read token from session files.
