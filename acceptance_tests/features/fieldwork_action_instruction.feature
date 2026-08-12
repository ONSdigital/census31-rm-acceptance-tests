Feature: Fieldwork action instruction forwarding

  Scenario: CREATE action instructions are published for non-N region new cases
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    Then CREATE fieldwork action instruction messages are emitted for all non-N region cases
    And the emitted CREATE fieldwork action instruction messages contain expected case and address fields

  Scenario: N region new cases are swallowed by the fieldwork adapter
    Given sample file "sample_1_input_nisra_census_spec.csv" is loaded successfully
    Then no fieldwork action instruction messages are emitted for N region cases

