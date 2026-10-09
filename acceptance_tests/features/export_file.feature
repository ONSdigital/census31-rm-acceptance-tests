Feature: Export files can be created with the correct data

  Scenario Outline: A case is loaded, action rule triggered and export file created with differing templates with UACs
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    When an export file action rule has been created for packcode "<template>" with no classifier
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]

    Examples:
      | sample file                          | template   |
      | sample_input_england_census_spec.csv | P_IC_ICL1  |

    @regression
    Examples:
      | sample file                             | template    |
      | sample_input_england_census_spec.csv    | P_IC_ICL2B  |
      | sample_input_england_census_spec.csv    | P_IC_H1     |
      | sample_input_england_census_spec.csv    | P_IC_H2     |
      | sample_1_input_england_census_spec.csv  | P_IC_ICL3   |
      | sample_1_input_england_census_spec.csv  | P_IC_ICL3A  |
      | sample_1_input_england_census_spec.csv  | P_RL_1RL1  |
      | sample_1_input_england_census_spec.csv  | P_RL_1RL2B |
      | sample_1_input_england_census_spec.csv  | P_RL_1RL3  |
      | sample_1_input_england_census_spec.csv  | P_RL_2RL1  |
      | sample_1_input_england_census_spec.csv  | P_RL_2RL2B |
      | sample_1_input_england_census_spec.csv  | P_RL_2RL3  |


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
      | sample_input_IRL_england_census_spec.csv    | P_RL_1RL1  | 9828ba30-b790-4aa6-8308-941e6bdf0616  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |


    @regression
    Examples:
      | sample file                                 | template    | action_rule_id                        | collection_exercise_id                |
      | sample_input_IRL_england_census_spec.csv    | P_RL_2RL1  | 99564451-e8af-4e92-9488-ac97d2aa3b4e  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_H2_wales_census_spec.csv       | P_IC_H2     | b68edc21-16fe-4de3-b0cf-d242d4ad7b13  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_ICL1_england_census_spec.csv   | P_IC_ICL1   | 2872997d-dc4e-4c8a-a539-671cbefe364b  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_ICL2_wales_census_spec.csv     | P_IC_ICL2B  | 46f12594-79d9-40e5-a11f-36845a3b497b  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_ICL3_scotland_census_spec.csv  | P_IC_ICL3   | 9d0f01ff-2838-4e08-8b0d-7e0268e0ba42  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  |
      | sample_input_IRL_wales_census_spec.csv      | P_RL_1RL2B | 069cc419-9308-4f38-b5ac-5a3444a03595  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_IRL_scotland_census_spec.csv   | P_RL_1RL3  | de2a0bc5-daa7-4bfb-acb7-19b3d5b9a8a4  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  |
      | sample_input_IRL_wales_census_spec.csv      | P_RL_2RL2B | 023a98a1-6217-4cad-b5ab-b1bf000dacc9  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  |
      | sample_input_IRL_scotland_census_spec.csv   | P_RL_2RL3  | 9c8415fd-fbad-4ad1-980d-2b6c8ae5f65a  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  |
      | sample_input_CE_scotland_census_spec.csv    | P_IC_ICL3A  | d234fc20-17bd-40ee-b263-feef5cf89840  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  |

  Scenario Outline: Export files can be produced using the classifiers from the pre-seeded 2027 no-UAC test action rules
    Given sample file "<sample file>" is loaded successfully
    And an export file template has been created with template "<template>"
    And the action rule with ID "<action_rule_id>" exists for collection exercise "<collection_exercise_id>"
    And the classifier is expected to export treatment codes "<exported_treatment_codes>" and filter "<filtered_treatment_codes>"
    When an export file action rule has been created for packcode "<template>" with the classifier from action rule "<action_rule_id>"
    Then an export file is created with correct rows
    And the events logged against the cases are ["NEW_CASE","EXPORT_FILE"]
    And only cases with expected treatment codes are exported

    Examples:
      | sample file                                  | template     | action_rule_id                        | collection_exercise_id                | exported_treatment_codes        | filtered_treatment_codes    |
      | sample_input_PCPR1_england_census_spec.csv   | P_IC_PCPR1   | 952d635b-f8d9-4c7e-85b9-7a5311e317df  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  | HH_PFE,HH_OFE,HH_ONE            | HH_PFW,HH_OFW,HH_ONW        |
      | sample_input_PCPR2B_wales_census_spec.csv    | P_IC_PCPR2B  | 78e404ec-13bc-48bb-ba5d-fd7cb2b9d475  | 1b9e4b45-fd33-922f-d39e-914d5bdabe84  | HH_PFW,HH_OFW,HH_ONW            | HH_PFE,HH_OFE,HH_ONE        |
      | sample_input_PCPR_scotland_census_spec.csv   | P_IC_PCPR13  | 1fda90c6-089a-47a0-90d4-952699816806  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  | HH_ONS                          | HH_PFE,HH_OFE,HH_PFW,HH_OFW |
      | sample_input_PCPR_scotland_census_spec.csv   | P_IC_PCPR23  | c18760f6-3f9c-4ffd-95d2-22d00962d6b7  | a6d57a19-2f53-3a10-f9f3-bc9eeb52dfb6  | HH_ONS                          | HH_PFE,HH_OFE,HH_PFW,HH_OFW |


  @reset_pubsub_queues
  Scenario: Export file headers are sanitised to ISD-compliant names
    Given sample file "sample_1_input_england_census_spec.csv" is loaded successfully
    And fulfilments are authorised for the export file template "P_OR_H2"
    And a print fulfilment has been requested
    And the events logged against the case are ["NEW_CASE", "PRINT_FULFILMENT"]
    When export file fulfilments are triggered to be exported
    Then UAC_UPDATE messages are emitted with active set to true
    And an export file is created with correct rows
    And the events logged against the case are ["NEW_CASE", "EXPORT_FILE", "PRINT_FULFILMENT"]
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
