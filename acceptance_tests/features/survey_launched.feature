Feature: Survey Launched from RH

  Scenario: Survey launched events are logged and the case flag is updated
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And an export file template has been created with template "ICL1"
    When an export file action rule has been created for packcode "ICL1"
    And UAC_UPDATE message is emitted with active set to true and "surveyLaunched" is false
    When an SURVEY_LAUNCHED event is received
    Then UAC_UPDATE message is emitted with active set to true and "surveyLaunched" is true
    And a CASE_UPDATE message is emitted where "surveyLaunched" is "True"
    And the events logged against the case are ["NEW_CASE","EXPORT_FILE","SURVEY_LAUNCHED"]
