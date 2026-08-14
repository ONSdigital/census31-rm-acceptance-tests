Feature: Fieldwork action instruction forwarding

  Scenario: CREATE action instruction messages are published for non-N regions new cases
    Given sample file "sample_input_non-nisra_census_spec.csv" is loaded successfully
    And an export file template has been created with template "P_IC_H1"
    When an export file action rule has been created for packcode "P_IC_H1"
    And UAC_UPDATE message is emitted with active set to true and "surveyLaunched" is false
    When SURVEY_LAUNCHED events are received for all emitted UACs
    Then UAC_UPDATE message is emitted with active set to true and "surveyLaunched" is true
    And CASE_UPDATE messages are emitted where "surveyLaunched" is "True" for all loaded cases
    And the events logged against the cases are ["NEW_CASE", "EXPORT_FILE", "SURVEY_LAUNCHED"]
    And CREATE fieldwork action instruction messages are emitted for all non-N region cases
    And the emitted CREATE fieldwork action instruction messages contain expected case and address fields

  Scenario: CREATE action instruction messages are not published for N region new cases
    Given sample file "sample_1_input_nisra_census_spec.csv" is loaded successfully
    And an export file template has been created with template "P_IC_H1"
    When an export file action rule has been created for packcode "P_IC_H1"
    And UAC_UPDATE message is emitted with active set to true and "surveyLaunched" is false
    When SURVEY_LAUNCHED events are received for all emitted UACs
    Then UAC_UPDATE message is emitted with active set to true and "surveyLaunched" is true
    And CASE_UPDATE messages are emitted where "surveyLaunched" is "True" for all loaded cases
    And the events logged against the cases are ["NEW_CASE", "EXPORT_FILE", "SURVEY_LAUNCHED"]
    And no fieldwork action instruction messages are sent for N region cases
