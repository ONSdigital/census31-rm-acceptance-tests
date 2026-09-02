"""Maps QID prefix to form type, matching the logic in case-processor's QidFormTypeHelper."""

_QID_PREFIX_TO_FORM_TYPE = {
    1: 'H', 2: 'H', 3: 'H', 4: 'H', 5: 'H',
    6: 'HA',
    7: 'HB',
    21: 'I', 22: 'I', 23: 'I', 24: 'I', 25: 'I',
    26: 'IA',
    27: 'IB',
}


def map_qid_to_form_type(qid: str) -> str | None:
    """Derive the expected form type from a QID's 2-character prefix."""
    if not qid or len(qid) < 2:
        return None
    try:
        questionnaire_type = int(qid[:2])
    except ValueError:
        return None
    return _QID_PREFIX_TO_FORM_TYPE.get(questionnaire_type)
