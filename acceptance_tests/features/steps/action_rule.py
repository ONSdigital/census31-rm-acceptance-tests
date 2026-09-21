from behave import step

from acceptance_tests.utilities.action_rule_helper import create_export_file_action_rule, get_action_rules
from acceptance_tests.utilities.test_case_helper import test_helper

@step('an export file action rule has been created for packcode "{packcode}" with no classifier')
def create_export_file_action_rule_no_classifiers(context, packcode):
    context.correlation_id = create_export_file_action_rule(context.collex_id, '', packcode, '')


@step('an export file action rule has been created for packcode "{packcode}" with the classifier fom action rule {action_rule_id}')
def create_export_file_action_rule_with_classifiers(context, packcode, action_rule_id):
    cleaned_pack_code = str(packcode).strip("'")
    cleaned_action_rule_id = str(action_rule_id).strip('"')
    matches = [record for record in context.action_rules if
               str(record.get("packCode")).strip('"') == cleaned_pack_code and str(record.get("actionRuleId")).strip("'") == cleaned_action_rule_id]
    test_helper.assertTrue(len(matches) > 0, 'Not found classifier for given pack code' )
    classifier = matches[0].get("classifiers")
    description =matches[0].get("description")
    context.correlation_id = create_export_file_action_rule(context.collex_id, classifier, packcode, description)


@step('the action rule with ID {actionRuleId} exists for collection exercise {collectionExerciseId}')
def check_action_rule_id_exists_for_collection_exercise_id(context, actionRuleId, collectionExerciseId):
    if not hasattr(context, 'action_rules') or context.action_rules is None:
        context.action_rules = get_action_rules(collectionExerciseId).json()
    cleaned_action_rule_id = str(actionRuleId).strip('"')
    cleaned_collex_id = str(collectionExerciseId).strip('"')
    matches = [record for record in context.action_rules if str(record.get("actionRuleId")).strip('"') == cleaned_action_rule_id and  str(record.get("collectionExerciseId")).strip('"') == cleaned_collex_id]
    test_helper.assertTrue(len(matches)>0, 'Not found action rule id and collection exercise id')

