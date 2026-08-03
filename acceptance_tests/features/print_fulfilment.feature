Feature: Print fulfilments can be requested for a case

  Scenario Outline: A print fulfilment is requested for a case
  Given sample file "<sample file>" is loaded successfully
  And fulfilments are authorised for the export file template "<template>"
  And a print fulfilment has been requested
  And the events logged against the case are ["NEW_CASE","PRINT_FULFILMENT"]
  When export file fulfilments are triggered to be exported
  Then UAC_UPDATE messages are emitted with active set to true
  And an export file is created with correct rows
  And the events logged against the case are ["NEW_CASE", "EXPORT_FILE", "PRINT_FULFILMENT"]

  Examples:
    | sample file                             | template |
    | sample_1_input_england_census_spec.csv  | P_OR_H2  |



  Scenario Outline: A print fulfilment including personalisation is requested for a case
  Given sample file "<sample file>" is loaded successfully
  And fulfilments are authorised for the export file template "<template>"
  And a print fulfilment with personalisation {"title":"Mr.", "forename":"Joe", "surname":"Bloggers"} has been requested
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
    | sample_1_input_england_census_spec.csv  | P_OR_I2    |
    | sample_1_input_england_census_spec.csv  | P_OR_I2W   |
    | sample_1_input_england_census_spec.csv  | P_OR_I2    |
    | sample_1_input_england_census_spec.csv  | P_OR_I2W   |
    | sample_1_input_england_census_spec.csv  | P_OR_IACR3 |









