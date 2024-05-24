# Technical_Trial_Sensor_Reader

## Getting started
The application can be run as a Docker container or directly from source code. In order to avoid compatibility issues and
installation of required libraries, it is recommended to use the Docker version. To build and run the Docker version, docker compose files has
been provided to simplify the process, which can be found in the `docker` folder.

> Note: To run the app from source code requires Python dependencies to be installed. User can install all requires packages by installing
a conda environment using the file `environment.yml`.
```
$ conda env update -f environment.yml
```

## Usage
Input arguments to the application can be modified in the dockerized version by changing them in an environment file,
which can be found in `docker/app_launch_arguments.env`.

Docker compose instructions has been included in the bash script `run.sh`. Being in the root directory, execute:
```
$ ./run.sh
```

Execution from source code can be done using the command:
```
$ python3 -m sensor_reader.app --sensor_type $SENSOR_TYPE --freq_read_data $FREQ_READ_DATA --uri_db_server $URI_DB_SERVER --min_range_value $MIN_RANGE_VALUE --max_range_value $MAX_RANGE_VALUE
```
> Note: Running the app by this way requires the user to mount external services (database and message server). To help in that process, the docker
compose file `docker/compose_external_services.yaml` can be used.

## Tests
Testing needs to mount external servers for some of the defined testing methods. This could've been improved by mounting those servers during the
tests by themself, but there was no time to accomplish this. To help in the mounting process, the bash script `test.sh` can be used.
Reporting of the coverage is included.
