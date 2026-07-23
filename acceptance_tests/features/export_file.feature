Feature: Export files can be created with the correct data

  Scenario Outline: A case is loaded, action rule triggered and export file created with differing templates with UACs
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    When an export file action rule has been created for packcode "<template>"
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]

    Examples:
      | sample file                          | template |
      | sample_input_england_census_spec.csv | ICL1     |
      | sample_input_england_census_spec.csv | ICL1-W   |

    @regression
    Examples:
      | sample file                          | template |
      | sample_input_england_census_spec.csv | 1RL1     |
      | sample_input_england_census_spec.csv | 1RL1-W   |
      | sample_input_england_census_spec.csv | 1RL2     |
      | sample_input_england_census_spec.csv | 1RL2-W   |

  Scenario Outline: A case is loaded, action rule triggered and export file created with a template with no UAC
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    When an export file action rule has been created for packcode "<template>"
    Then an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]

    Examples:
      | sample file                          | template |
      | sample_input_england_census_spec.csv | PC       |
      | sample_input_england_census_spec.csv | PC-W     |