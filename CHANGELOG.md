# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2023-05-25

### Changed

a complete refactor cleanup

- remove unused function
- remove unused code lines
- update readme and infos
- update pkg which needs to be installed
- update test script and dev pkg which needs to be install
- add python config scripts like pyproject.toml
- update base info file for new and detail info, like github script, sec, ...
- logging is updated
- fix and improve api usage for clockify and youtrack
  - code is more clean
  - youtrack time for check if uploaded should be fixed (but not sure ^^)
  - add option to clockify to use auto calc buffer issue
- and some more refactoring

## [0.0.2] - 2021-11-17

### Added

- api usage for youtrack
  - saved file in temp, will imported into youtrack

### Changed

- time-entries
  - get combined list of work
  - save into temp, for usage in ex.: youtrack or jira
- improve code

## [0.0.1] - 2021-11-05

### Added

- api usage for clockify
  - user
  - time-entries
- parser for result
  - print times in combined format
    > to use in ex.: youtrack/jira/...

[unreleased]: https://github.com/MVladislav/vm-clockify/compare/v1.0.0...HEAD
[0.0.1]: https://github.com/MVladislav/vm-clockify/releases/tag/v0.0.1
