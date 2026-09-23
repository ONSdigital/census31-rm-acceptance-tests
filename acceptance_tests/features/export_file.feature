Feature: Export files can be created with the correct data

  Scenario Outline: A case is loaded, action rule triggered and export file created with differing templates with UACs
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    When an export file action rule has been created for packcode "<template>" with no classifier
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]

    Examples:
      | sample file                          | template |
      | sample_input_england_census_spec.csv | P_IC_ICL1  |
      | sample_input_england_census_spec.csv | P_IC_ICL2B |

    @regression
    Examples:
      | sample file                             | template    |
      | sample_input_england_census_spec.csv    | P_IC_H1     |
      | sample_input_england_census_spec.csv    | P_IC_H2     |
      | sample_1_input_england_census_spec.csv  | P_IC_ICL3   |
      | sample_1_input_england_census_spec.csv  | P_IC_ICL3A  |
      | sample_1_input_england_census_spec.csv  | P_RL_1IRL1  |
      | sample_1_input_england_census_spec.csv  | P_RL_1IRL2B |
      | sample_1_input_england_census_spec.csv  | P_RL_1IRL3  |
      | sample_1_input_england_census_spec.csv  | P_RL_2IRL1  |
      | sample_1_input_england_census_spec.csv  | P_RL_2IRL2B |
      | sample_1_input_england_census_spec.csv  | P_RL_2IRL3  |


  Scenario Outline: A case is loaded, action rule triggered and export file created with a template with no UAC
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    When an export file action rule has been created for packcode "<template>" with no classifier
    Then an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]

    Examples:
      | sample file                          | template    |
      | sample_input_england_census_spec.csv | P_IC_PCPR1  |

    @regression
    Examples:
      | sample file                             | template     |
      | sample_1_input_england_census_spec.csv  | P_IC_PCPR2B  |
      | sample_1_input_england_census_spec.csv  | P_IC_PCPR13  |
      | sample_1_input_england_census_spec.csv  | P_IC_PCPR23  |

  Scenario Outline: Export files can be produced using the classifiers from the pre-seeded 2027 test action rules
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    And the action rule with ID "<action_rule_id>" exists for collection exercise "<collection_exercise_id>"
    When an export file action rule has been created for packcode "<template>" with the classifier from action rule "<action_rule_id>"
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]

    Examples:
      | sample file                                 | template    | action_rule_id                        | collection_exercise_id                |
      | sample_input_H1_england_census_spec.csv     | P_IC_H1     | 8aee5ac7-60d3-43c8-81be-e30bf6055ae8  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |

    @regression
    Examples:
      | sample file                                 | template    | action_rule_id                        | collection_exercise_id                |
      | sample_input_H2_wales_census_spec.csv       | P_IC_H2     | b68edc21-16fe-4de3-b0cf-d242d4ad7b13  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_ICL1_england_census_spec.csv   | P_IC_ICL1   | 2872997d-dc4e-4c8a-a539-671cbefe364b  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_ICL2_wales_census_spec.csv     | P_IC_ICL2B  | 46f12594-79d9-40e5-a11f-36845a3b497b  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_ICL3_scotland_census_spec.csv  | P_IC_ICL3   | 9d0f01ff-2838-4e08-8b0d-7e0268e0ba42  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  |

  @reset_pubsub_queues
  Scenario: Export file headers are sanitised to ISD-compliant names
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And fulfilments are authorised for the export file template "P_OR_H2"
    And a print fulfilment has been requested
    When export file fulfilments are triggered to be exported
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the export file header row is sanitised according to:
      | template_key         | header_name |
      | __pack_code__        | PRODUCTPACK_CODE |
      | __uac__              | UAC         |
      | __qid__              | QID         |
      | __welsh_uac__        | WALES_UAC   |
      | __welsh_qid__        | WALES_QID   |
      | __caseref__          | CASEREF     |
      | __request__.title    | TITLE       |
      | __request__.forename | FORENAME    |
      | __request__.surname  | SURNAME     |
      | ADDRESS_LINE1        | ADDRESS_LINE1 |
      | ADDRESS_LINE2        | ADDRESS_LINE2 |
      | ADDRESS_LINE3        | ADDRESS_LINE3 |
      | TOWN_NAME            | TOWN_NAME   |
      | POSTCODE             | POSTCODE    |
