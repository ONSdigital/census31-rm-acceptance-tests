Feature: Print fulfilments can be requested for a case


  Scenario Outline: A print fulfilment including personalisation is requested for a case
  Given sample file "<sample file>" is loaded successfully
  And fulfilments are authorised for the export file template "<template>"
  And a print fulfilment with personalisation {"title":"Mr.", "forename":"Joe", "surname":"Bloggs"} has been requested
  And the events logged against the case are ["NEW_CASE", "PRINT_FULFILMENT"]
  When export file fulfilments are triggered to be exported
  Then UAC_UPDATE messages are emitted with active set to true
  And an export file is created with correct rows
  And the events logged against the case are ["NEW_CASE", "EXPORT_FILE", "PRINT_FULFILMENT"]

  Examples:
    | sample file                             | template |
    | sample_1_input_england_census_spec.csv  | P_OR_I1  |

  @regression
    Examples:
    | sample file                             | template   |
    | sample_1_input_england_census_spec.csv  | P_OR_H1    |
    | sample_1_input_england_census_spec.csv  | P_OR_H2    |
    | sample_1_input_england_census_spec.csv  | P_OR_I2    |
    | sample_1_input_england_census_spec.csv  | P_OR_I2W   |
    | sample_1_input_england_census_spec.csv  | P_OR_IACR3 |


  @reset_notify_stub
  Scenario Outline: A SMS fulfilment is requested for a case
    Given sample file "<sample file>" is loaded successfully
    And fulfilments are authorised for sms template "<template>"
    When a request has been made for a UAC by SMS from phone number "07123456780"
    Then UAC_UPDATE messages are emitted with active set to true
    And the events logged against the case are ["NEW_CASE","SMS_FULFILMENT"]
    And notify api was called with the correct SMS template and values

    Examples:
      | sample file                            | template |
      | sample_1_input_england_census_spec.csv | UACHHT1  |

    @regression
    Examples:
      | sample file                            | template |
      | sample_1_input_england_census_spec.csv | UACHHT2  |
      | sample_1_input_england_census_spec.csv | UACHHT2W |
      | sample_1_input_england_census_spec.csv | UACHHT3  |
      | sample_1_input_england_census_spec.csv | UACHHT4  |
      | sample_1_input_england_census_spec.csv | UACIT1   |
      | sample_1_input_england_census_spec.csv | UACIT2   |
      | sample_1_input_england_census_spec.csv | UACIT2W  |
      | sample_1_input_england_census_spec.csv | UACIT3   |
      | sample_1_input_england_census_spec.csv | UACIT4   |
