"""
Entry point for lambda
"""
from _ebcf_alexa import interaction_model
import logging

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)

def lambda_handler(event, context) -> dict:
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    LOG.info("Start Lambda Event for event.session.application.applicationId=%s",
             event['session']['application']['applicationId'])

    # This is the official application id
    if (event['session']['application']['applicationId'] !=
            'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'):
        raise ValueError("Invalid Application ID")

    request_type = event['request']['type']
    try:
        handler = interaction_model.REQUEST_HANDLERS[request_type]
    except KeyError:
        LOG.error('Unknown request type: %s', request_type)
        raise ValueError('Unknown Request Type')
    speechlet = handler(event['request'], event['session'])
    return speechlet.dict()
