# CHANGELOG

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
