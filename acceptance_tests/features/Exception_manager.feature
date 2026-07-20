Feature: Check exception manager is called for every topic and handles them as expected

  # Scenario labelled 1 as we want this one to run at the beginning of the tests as a way of warming up pubsub
  Scenario: 1: A Bad Json Msg sent to every topic, msg arrives in exception manager
    When a bad json msg is sent to every topic consumed by RM
    Then each bad msg is seen by exception manager with the message containing "com.fasterxml.jackson.core.JsonParseException"
    And each bad msg can be successfully quarantined

  @regression
  Scenario: Bad survey launched message turns up in exception manager
    When a bad Survey Launched event is put on the topic
    Then a bad message appears in exception manager with exception message containing "qid '555555' not found!"
    And each bad msg can be successfully quarantined

