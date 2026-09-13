Feature: A case can be refused with an event

  @regression
  Scenario: A case is loaded and can be refused
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    When a refusal event is received
    Then a CASE_UPDATE message is emitted where "refusalReceived" is "HARD_REFUSAL"
    And the events logged against the case are ["NEW_CASE","REFUSAL_RECEIVED"]
    And the CANCEL fieldwork action instruction message is emitted for the case
