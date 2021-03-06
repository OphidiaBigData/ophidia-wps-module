
## v1.2.0 - 2021-03-11

### Added:

- Support for PyWPS 4 [#1](https://github.com/OphidiaBigData/ophidia-wps-module/pull/1)

### Removed:

- Support for PyWPS 3

## v1.1.1 - 2021-03-11

### Added:

- New parameter 'cubes' to OPH_INTERCUBE

### Changed:

- Name of parameter 'return' to 'return_code'
- Process format for PyWPS 4

### Removed:

- Support for 'base64' encoding, except for the process 'ophexecutemain'

## v1.1.0 - 2019-01-24

### Fixed:

- command name associated with OPH_CLUSTER

### Added:

- argument 'user_filter' to OPH_CLUSTER
- process associated with OPH_CONCATNC
- process associated with OPH_CONCATNC2
- argument 'algorithm' to OPH_CUBESIZE
- argument 'container_pid' to OPH_DELETECONTAINER
- argument 'algorithm' to OPH_RANDCUBE
- process associated with OPH_RANDCUBE2
- arguments 'subset_filter' and 'offset' to OPH_SET

### Changed:

- argument 'action' of OPH_CLUSTER
- argument 'operation' of OPH_INTERCUBE

### Removed:

- arguments 'delete_type' and 'hidden' from OPH_DELETECONTAINER
- arguments 'filesystem', 'ndbms' and 'ndb' from OPH_IMPORTFITS
- arguments 'filesystem', 'ndbms' and 'ndb' from OPH_IMPORTNC
- arguments 'filesystem', 'ndbms' and 'ndb' from OPH_IMPORTNC2
- argument 'hidden' from OPH_LIST
- arguments 'filesystem', 'ndbms' and 'ndb' from OPH_RANDCUBE
- process associated with OPH_RESTORECONTAINER

## v1.0.0 - 2018-07-27

- Add a specific process for each operator

## v0.1.0 - 2016-10-25

- Initial public release

