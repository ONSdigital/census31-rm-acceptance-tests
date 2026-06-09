# Code Standards and Style Guide

## Format

Our base code style is [PEP8](https://www.python.org/dev/peps/pep-0008/), but we allow a max line length of 120.

Check formatting and dead code with

```shell
make lint
```

## Code Standards

### Context Use

We make use of the [Behave Context](https://behave.readthedocs.io/en/stable/tutorial.html#context) object to store data
that is needed across multiple steps of a scenario.

To prevent the context from becoming cluttered and confusing to use, we define some rules for how we interact with it:

#### Only step functions and environment hooks should interact with the context attributes

Other none step or hook functions shouldn't be passed the entire context and should certainly not modify it. Instead,
pass in explicit variables from the context and return new ones as required. Try to make all none step functions
pure/deterministic.

e.g.

```python
@step('a thing happens')
def step_to_do_a_thing(context):
    context.some_var = helper_function(context.emitted_cases[0])
```

#### Context Index

Every context attribute used by the tests must be described here. This table is parsed into the code to drive audit
logging upon failure in the [audit_trail_helper](/acceptance_tests/utilities/audit_trail_helper.py).

<div id="context-index-table">

| Attribute                          | Description                                                                         | Type     |
|------------------------------------|-------------------------------------------------------------------------------------|----------|
| test_start_utc_datetime            | Stores the UTC time at the beginning of each scenario in an environment hook        | datetime |
| survey_id                          | Stores the ID of the survey generated and or used by the scenario                   | UUID     |
| collex_id                          | Stores the ID of the collection exercise generated and or used by the scenario      | UUID     |
| collex_end_date                    | Stores the UTC time for a collection exercise end date                              | datetime |
| emitted_cases                      | Stores the caseUpdate DTO objects emitted on `CASE_UPDATE` events                   | List     |
| emitted_uacs                       | Stores the UAC DTO objects from the emitted `UAC_UPDATE` events                     | List     |
| pack_code                          | Stores the pack code used for fulfilments or action rules                           | str      |
| template                           | Stores the column template used for fulfilments or action rules                     | Template |
| export_supplier                    | Stores the export file supplier name the pack_code fo the current test is linked to | str      |
| notify_template_id                 | Stores the ID of the sms template used for the notify service                       | UUID     |
| fulfilment_response_json           | Stores the response JSON from a `POST` to the Notify API                            | Dict     |
| phone_number                       | Stores the phone number needed to check the notify api                              | str      |
| email                              | Stores the email address needed to check the notify api                             | str      |
| message_hashes                     | Stores the hash of sent messages, for testing exception management                  | List     |
| correlation_id                     | Stores the ID which connects all related events together                            | UUID     |
| originating_user                   | Stores the email of the ONS employee who originally initiated a business event      | str      |
| sent_messages                      | Stores every scenario sent message for debugging errors                             | List     |
| scenario_name                      | Stores the scenario name and uses it for unique originating users in messages       | str      |
| case_id                            | Stores the case_id of a case used in the scenario                                   | UUID     |
| bulk_refusals                      | Stores created bulk refusal cases we expect to see messages for                     | List     |
| bulk_invalids                      | Stores the create bulk invalid cases we expect to see messages for                  | List     |
| bulk_sample_update                 | Stores the create bulk sample update cases we expect to see messages for            | List     |
| bulk_sensitive_update              | Stores the bulk sensitive update cases we expect to see messages for                | List     |
| expected_collection_instrument_url | Stores the collection instrument URL expected on emitted `UAC_UPDATE` events        | str      |
| fulfilment_personalisation         | Stores the personalisation values from a received fulfilment request event          | Dict     |
| sample                             | Stores the parsed sample file rows, split into `sample` and `sensitive`             | List     |
| email_templates                    | Stores the list of email templates setup prior to the tests                         | Mapping  |
| email_packcodes                    | Stores the list of email packcodes setup prior to the tests                         | Mapping  |
| export_file_templates              | Stores the list of export file templates setup prior to the tests                   | Mapping  |
| export_file_packcodes              | Stores the list of export packcodes setup prior to the tests                        | Mapping  |
| sms_templates                      | Stores the list of sms templates setup prior to the tests                           | Mapping  |
| sms_packcodes                      | Stores the list of sms packcodes setup prior to the tests                           | Mapping  |
| survey_name                        | Stores the survey name to be used in the scenario                                   | str      |
| edited_survey_name                 | Stores the edited survey name to be used in the scenario                            | str      |
| collection_exercise_name           | Stores the collection exercise name to be used in the scenario                      | str      |
| edited_collection_exercise__name   | Stores the edited collection exericise name to be used in the scenario              | str      |
| cohort                             | Stores the cohort number to be used in action scenarios                             | int      |
| sample_file                        | Stores the sample file name to be used in the scenario                              | str      |

</div>

### Sharing Code Between Steps

Step files should not import code from other step files, where code can be shared between steps they should either be in
the same file, or the shared code should be factored out into the utilities module.

### Step wording

Steps should be written in full and concise sentences, avoiding unnecessary abbreviations and shorthand. They should be
as understandable and as non-technical as possible.

### Assertions

Assertions should use the [`test_helper`](acceptance_tests/utilities/test_case_helper.py) assertion methods and should
always include a message with relevant explanation and data where it is useful.

### Step parameter types

Where we need [step parameters](https://behave.readthedocs.io/en/stable/tutorial.html#step-parameters) to include more
complex data than single strings or the other basic types supported by the default parser, we
use [custom registered types](https://behave.readthedocs.io/en/stable/api.html#behave.register_type). These are
registered in the [environment.py](acceptance_tests/features/environment.py) so they are available to all steps.

For example, our `json` type lets us write JSON data in the steps which will be parsed into python objects like so:

```python
@step('this step receives a json parameter {foo:json}')
def example(foo):
    pass
```

This example step could be called with a JSON object which will be parsed into a dictionary:

```gherkin
When this step receives a json parameter {"spam": "eggs"}
```

And our `array` type allows us to parse JSON arrays into python lists, e.g.

```python
@step('this step receives an array parameter {foo:array}')
def example(bar: List):
    pass
```

```gherkin
When this step receives an array parameter ["spam", "eggs"]
```

### SMS/Print/Email Templates

The templates used for action rules and fulfilments are set up in the `before_all` environment step prior to whatever
test(s) are running so that they can be used repeatedly.
The templates are held in .json files within the `resources/template_files` directory and there is a file for each of
the type.

The template format is a list, and this list holds the fields to be included on the template, for example a template
consisting of a sensitive email address and a uac would look like:

```["__sensitive__.emailAddress","__uac__"]```

The corresponding format to use the template in a feature step would be:

```"sensitive_emailaddress__uac"```

So to add a new template, find the appropriate .json file and add a new block, add the template list to the template
value, and the templateName value would be the list but converted so it is single underscore where there would be dot
notation, and double underscores to show the gap between two list items as can be seen above between email address and
uac.