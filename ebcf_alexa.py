"""
Entry point for lambda
"""
from _ebcf_alexa import interaction_model, incoming_types, speechlet
import logging

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
ALEXA_SKILL_ID = 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'


def lambda_handler(event_dict: dict, context) -> dict:
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    LOG.debug(repr(event_dict))
    event = incoming_types.LambdaEvent(event_dict)
    LOG.info("Start Lambda Event for event.session.application.applicationId=%s",
             event.session.application.application_id)

    # This is the official application id
    if event.session.application.application_id != ALEXA_SKILL_ID:
        raise ValueError("Invalid Application ID: %s" % event.session.application.application_id)

    return interaction_model.handle_event(event).dict()

