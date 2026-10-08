Feature: Receipt an RM questionnaire directly from an eQ submission message

  Scenario: An eQ receipt uses the questionnaire ID and transaction ID, not the supplied case ID
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And an export file template has been created with template "P_IC_ICL1"
    When an export file action rule has been created for packcode "P_IC_ICL1" with no classifier
    And UAC_UPDATE message is emitted with active set to true
    When an eQ receipt with a transaction ID and unrelated case ID is published
    Then UAC_UPDATE message is emitted with active set to false
    And a CASE_UPDATE message is emitted where "receiptReceived" is "True"
    And the eQ receipt audit has the expected correlation ID
    And the events logged against the case are ["NEW_CASE","EXPORT_FILE","RESPONSE_RECEIVED"]

  @regression
  Scenario: An eQ receipt without a transaction ID generates a correlation ID
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And an export file template has been created with template "P_IC_ICL1"
    When an export file action rule has been created for packcode "P_IC_ICL1" with no classifier
    And UAC_UPDATE message is emitted with active set to true
    When an eQ receipt without a transaction ID is published
    Then the eQ receipt has a generated correlation ID
    And UAC_UPDATE message is emitted with active set to false
    And a CASE_UPDATE message is emitted where "receiptReceived" is "True"
    And the eQ receipt audit has the expected correlation ID
    And the events logged against the case are ["NEW_CASE","EXPORT_FILE","RESPONSE_RECEIVED"]
