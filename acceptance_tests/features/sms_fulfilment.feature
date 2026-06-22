Feature: Sms fulfilment

  @reset_notify_stub
  Scenario Outline: A SMS fulfilment is requested for a case
    Given sample file "<sample file>" is loaded successfully
    And fulfilments are authorised for sms template "<template>"
    When a request has been made for a UAC by SMS from phone number "<phone number>"
    Then UAC_UPDATE messages are emitted with active set to true
    And the UAC_UPDATE message matches the SMS fulfilment UAC
    And the events logged against the case are ["NEW_CASE","SMS_FULFILMENT"]
    And notify api was called with the correct SMS template and values

    Examples:
      | sample file                            | template | phone number |
      | sample_1_input_england_census_spec.csv | UACHHT1  | 07123456789  |

    @regression
    Examples:
      | sample file                            | template | phone number |
      | sample_1_input_england_census_spec.csv | UACHHT2  | 07123456789  |
