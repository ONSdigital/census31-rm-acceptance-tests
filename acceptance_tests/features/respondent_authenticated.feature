Feature: Respondent Authenticated from RH

  Scenario: Respondent authenticated events are logged without updating case flags
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And an export file template has been created with template "P_IC_ICL1"
    When an export file action rule has been created for packcode "P_IC_ICL1"
    And UAC_UPDATE messages are emitted with active set to true
    When a RESPONDENT_AUTHENTICATED event is received
    Then the events logged against the case are ["NEW_CASE","EXPORT_FILE","RESPONDENT_AUTHENTICATED"]
