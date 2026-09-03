Feature: Mark the case as receipted when receipt received message event is received

  Scenario: EQ response received events are logged and the case flag is updated
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And an export file template has been created with template "P_IC_ICL1"
    When an export file action rule has been created for packcode "P_IC_ICL1"
    And UAC_UPDATE messages are emitted with active set to true
    When a Receipt event is received
    Then UAC_UPDATE messages are emitted with active set to false
    And a CASE_UPDATE message is emitted where "receiptReceived" is "True"
    And the events logged against the case are ["NEW_CASE","EXPORT_FILE","RECEIPT"]
