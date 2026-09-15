Feature: Field follow-up filtering - Cases excluded from fieldwork

  Scenario: Region-based filtering
    Given sample file "sample_field_eligibility_cases.csv" is loaded successfully
    When field follow-up messages are checked for the following cases:
      | case_id     | outcome  | reason                                                     |
      | 10008677204 | filtered | region N92000002 (NISRA) excluded from field follow-up     |
      | 10008677205 | filtered | region S92000003 (Scotland) excluded from field follow-up  |
      | 10008677209 | filtered | region N92000002 (NISRA) excluded from field follow-up     |
      | 10008677207 | passed   | region W92000004 (Wales) eligible for field follow-up      |
      | 10008677208 | passed   | region E12000009 (England) eligible for field follow-up    |

  Scenario: Valid cases pass regardless of treatment code variety
    Given sample file "sample_field_eligibility_cases.csv" is loaded successfully
    When field follow-up messages are checked for the following cases:
      | case_id     | outcome | reason                                    |
      | 10008677190 | passed  | valid HH case with HH_PSCE treatment code |
      | 10008677191 | passed  | valid HH case with HH_PSLE treatment code |
      | 10008677192 | passed  | valid HH case with HH_PNCE treatment code |
      | 10008677193 | passed  | valid HH case with HH_OSCE treatment code |
      | 10008677194 | passed  | valid HH case with HH_ONCE treatment code |
      | 10008677195 | passed  | valid HH case with HH_PSCW treatment code |
      | 10008677196 | passed  | valid HH case with HH_PSLW treatment code |
      | 10008677197 | passed  | valid HH case with HH_OSXS treatment code |
      | 10008677206 | passed  | valid HH case with HH_PSCE treatment code |

  Scenario: A receipted English household case update is not sent to field
    Given sample file "sample_field_eligibility_cases.csv" is loaded successfully
    When a receipted CASE_UPDATE is published for UPRN "10008677206"
    Then a CASE_UPDATE message is emitted where "receiptReceived" is "True"
    And no fieldwork action instruction is sent for the receipted case
