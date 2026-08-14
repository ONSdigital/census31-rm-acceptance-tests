Feature: Sample files of all accepted shapes can be loaded

  Scenario: A sample file is loaded
    Given sample file "sample_input_england_census_spec.csv" is loaded successfully
    And CREATE fieldwork action instruction messages are emitted for all non-N region cases
    And the emitted CREATE fieldwork action instruction messages contain expected case and address fields