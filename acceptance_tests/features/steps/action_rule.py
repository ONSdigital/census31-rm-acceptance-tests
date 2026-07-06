from behave import step

from acceptance_tests.utilities.action_rule_helper import create_export_file_action_rule


@step('an export file action rule has been created for packcode "{packcode}"')
def create_export_file_action_rule_no_classifiers(context, packcode):
    context.correlation_id = create_export_file_action_rule(context.collex_id, '', packcode)
