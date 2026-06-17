Feature: Export files can be created with the correct data

  Scenario: A case is loaded, action rule triggered and export file created with differing templates with UACs
    Given sample file "sample_input_england_census_spec.csv" is loaded successfully
    And an export file template has been created with template "address_line1__address_line2__postcode__uac"
    When an export file action rule has been created
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]
