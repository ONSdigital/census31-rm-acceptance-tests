from typing import Iterable

from acceptance_tests.utilities.test_case_helper import test_helper


def build_expected_fulfilment_personalisation(template: Iterable[str], case, request_personalisation={}, uac_hash=None,
                                              qid=None):
    expected_personalisation = {}
    for template_item in template:
        if template_item == '__uac__':
            # The actual personalisation values with have the original UAC, but the test has access to the hash
            test_helper.assertIsNotNone(uac_hash, 'Fulfilment template includes a UAC but one was not supplied'
                                                  ' to build expected personalisation')
            expected_personalisation['__uac_hash__'] = uac_hash

        elif template_item == '__qid__':
            test_helper.assertIsNotNone(qid, 'Fulfilment template includes a QID but one was not supplied'
                                             ' to build expected personalisation')
            expected_personalisation[template_item] = qid

        elif template_item.startswith('__request__.'):
            if request_value := request_personalisation.get(template_item[len('__request__.'):]):
                expected_personalisation[template_item] = request_value

        else:
            expected_personalisation[template_item] = case['sample'][template_item]

    return expected_personalisation
