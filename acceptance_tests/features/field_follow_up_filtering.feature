Feature: Field follow-up filtering - Cases excluded from fieldwork

  Scenario: Region-based filtering
    Given sample file "sample_field_eligibility_cases.csv" is loaded successfully
    When field follow-up messages are checked for the following cases:
      | uprn        | outcome  | reason                                                     |
      | 10008677204 | filtered | region N92000002 (NISRA) excluded from field follow-up     |
      | 10008677205 | filtered | region S92000003 (Scotland) excluded from field follow-up  |
      | 10008677209 | filtered | region N92000002 (NISRA) excluded from field follow-up     |
      | 10008677207 | passed   | region W92000004 (Wales) eligible for field follow-up      |
      | 10008677208 | passed   | region E12000009 (England) eligible for field follow-up    |

  Scenario: Valid cases pass regardless of treatment code variety
    Given sample file "sample_field_eligibility_cases.csv" is loaded successfully
    When field follow-up messages are checked for the following cases:
      | uprn        | outcome | reason                                    |
      | 10008677190 | passed  | valid HH case with HH_PFE treatment code |
      | 10008677191 | passed  | valid HH case with HH_OFE treatment code |
      | 10008677192 | passed  | valid HH case with HH_OANN treatment code |
      | 10008677193 | passed  | valid HH case with HH_PFW treatment code |
      | 10008677194 | passed  | valid HH case with HH_OFW treatment code |
      | 10008677195 | passed  | valid HH case with HH_OBNN treatment code |
      | 10008677196 | passed  | valid HH case with HH_ONS treatment code |
      | 10008677197 | passed  | valid HH case with HH_PBNN treatment code |
      | 10008677206 | passed  | valid HH case with HH_PFE treatment code |

  Scenario: Online-only treatment codes are excluded from fieldwork
    Given sample file "sample_field_eligibility_cases.csv" is loaded successfully
    When field follow-up messages are checked for the following cases:
      | uprn        | outcome  | reason                                                     |
      | 10008677198 | filtered | HH_ONE treatment code excluded from field follow-up       |
      | 10008677199 | filtered | HH_ONW treatment code excluded from field follow-up       |
