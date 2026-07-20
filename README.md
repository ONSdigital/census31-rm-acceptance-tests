# census-rm-acceptance-tests

The Python Behave BDD tests for Census RM

## Run the tests locally against census-rm-docker-dev

1. Clone [census-rm-docker-dev](https://github.com/ONSdigital/census-rm-docker-dev) and run `make up` to start the required
   services

2. Run all the RM tests:
    ```shell
    make test
    ```

### Core Tests

To run just the core tests, those not marked @regression Run:

```shell
make run_tests_core
```

## Run tests against a GCP project

Run the `run_gke.sh` bash script like so, where `ENV` is the environment name suffix in the project name,
like `c31-sandbox-<ENV>`:

```shell
ENV=<YOUR_ENV_SUFFIX> ./run_gke.sh
```

**NB:** assumes infrastructure and RM services exist in respective projects.

By default, this will run the core RM tests, you can run the full suite of RM regression tests with:

```shell
ENV=<YOUR_ENV_SUFFIX> REGRESSION=true ./run_gke.sh
```

By default the script will use the `latest` tagged acceptance tests image, you can optionally pass in a custom image tag
like so to override it:

```shell
ENV=<YOUR_ENV_SUFFIX> ./run_gke.sh <custom_image_tag>
```

### With Local Changes

To run a locally-modified version of the acceptance tests in a pod you will have to build and tag the image, push it to
the GCR and change the image in [acceptance_tests_pod.yml](./acceptance_tests_pod.yml) to point to your modified image
tag.


```shell script
IMAGE_TAG=<YOUR_TAG>
make build
docker tag <Initial image tag> <New image tag>
docker push <new image tag>
```

Then run the tests with the run GKE script.

## Tests Configuration

Default behave config is provided in [.behaverc](/.behaverc). To run with custom configuration you can edit this file or
override settings with command line args. See the [Using Behave](https://behave.readthedocs.io/en/stable/behave.html)
page for details.

### Running in the IDE

To run the scenarios locally within an IDE you must have the environment variable `PUBSUB_EMULATOR_HOST=localhost:8538`
set.

For Pycharm, a default run configuration template is provided (in [.run](.run)) for the Behave run template, which sets
this variable for you. Providing you are running all the required services already, you should simply be able to run or
debug any feature or scenario within PyCharm without any further configuration.

### Custom Local Test Runs

To run with custom settings locally you will need to set the environment variable `PUBSUB_EMULATOR_HOST=localhost:8538`,
either in your environment or prefacing the call to behave.

The tests can be run by calling the behave command line tool through pipenv (after installing dependencies
with `pipenv install --dev`) like so:

```shell
PUBSUB_EMULATOR_HOST=localhost:8538 pipenv run behave acceptance_tests/features
```

You could alternatively activate the pipenv shell with `pipenv shell` in this project then call the `behave` tool
directly.

This can be uses to run individual feature files from the command line:

```shell
PUBSUB_EMULATOR_HOST=localhost:8538 pipenv run behave acceptance_tests/features/social.feature
```

Or to run with a custom combination of tags like so:

```shell
PUBSUB_EMULATOR_HOST=localhost:8538 pipenv run behave acceptance_tests/features --tags "~@regression" 
```

**NOTE** that tags combined in a single arg like  `--tags @foo,@bar` are combined with a logical `OR` whereas tags
provided in multiple args like `--tags @foo --tags @bar` are combined with an `AND`, and multiple negative tags
like `~@foo` can only be combined with `AND` in multiple, separate tags args.
See [Behave Tag Expressions](https://behave.readthedocs.io/en/stable/behave.html#tag-expression).

### PubSub Pull Timeout

The default timeout on the tests waiting for expected PubSub messages is set long to improve reliability in
potentially "cold" cloud environments. However, this may be impractical for local runs or development as the tests may
be very slow to fail. You can override this by setting `PUBSUB_DEFAULT_PULL_TIMEOUT` in the test environment to a
smaller value such as `10` (seconds), since a local PubSub emulator or "warmed up" cloud environment should not need
such a long wait for messages.

### Exception test naming
All feature files have been named with all lower case titles. The one exception is the `Exception_manager.feature` test file. This is because we want this test to run at the beginning of the test run, and behave will execure feature files that are capitalised before files named with lower case titles.
The reason we want this test to run first is to help warmup a cold pubsub in the CI environment. This test uses all the pubsub topics and services. It also utilises some waits, so it should work as a good test to run to ensure pubsub is fully warmed up when the rest of the tests run.

### Test Keys

For development environments, the services is configured to use the dummy test keys
from [census31-rm-docker-dev](https://github.com/ONSdigital/census31-rm-docker-dev) by default, assuming the repository
is in the same parent directory.

See [census31-rm-docker-dev Test keys](https://github.com/ONSdigital/census31-rm-docker-dev#test-keys) for details.
