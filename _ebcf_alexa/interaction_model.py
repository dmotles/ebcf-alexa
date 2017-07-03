"""
Interaction Model

This module basically maps out the response tree for the skill.
"""
from datetime import timedelta, datetime, date
from operator import attrgetter
from typing import Union
from textwrap import dedent
import logging
from . import wods
from . import speechlet
from . import env

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def _get_speech_date(d: Union[date, datetime]) -> str:
    return '{} {}, {}'.format(d.strftime('%A %B'), d.day, d.year)


def _confirm_choice(should_confirm: bool, relative_qualifier: str, query: str) -> str:
    if should_confirm:
        if relative_qualifier:
            return '<p>OK, {}\'s {}</p>'.format(relative_qualifier, query)
        return '<p>OK, {}.</p>'.format(query)
    return ''


def _wod_ssml(wod: wods.WOD) -> str:
    if wod:
        if wod.publish_datetime > env.now():
            return '<p>The wod for {} has not been posted yet.</p>'.format(_get_speech_date(wod.date))
        return wod.full_ssml()
    return '<p>There is no workout.</p>'


def _wod_card(wod: wods.WOD, relative_qualifier: str, query_type: str) -> speechlet.SimpleCard:
    card_content = wod.pprint()
    card_title = '{} for {}'.format(query_type, relative_qualifier) if relative_qualifier else query_type
    if wod.image:
        return speechlet.StandardCard(title=card_title, content=card_content, large_image_url=wod.image)
    return speechlet.SimpleCard(title=card_title, content=card_content)


def goodbye(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    return end_session()


def end_session() -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        speechlet.PlainText('Goodbye.'),
        should_end=True
    )


def query_intent(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    """
    Responds to most queries of the skill.
    :param intent:
    :param attributes:
    :return:
    """
    try:
        relative_qualifier = intent['slots']['RelativeQualifier']['value']
    except KeyError:
        relative_qualifier = None
    try:
        query_type = intent['slots']['Query']['value']
    except KeyError:
        query_type = None

    wod = wods.get_wod(env.localdate())
    ssml = speechlet.SSML(
        '<speak>' +
        _confirm_choice(attributes.get('confirm_choice', False), relative_qualifier, query_type) +
        _wod_ssml(wod)
    )
    card = _wod_card(wod, relative_qualifier, query_type)
    return speechlet.SpeechletResponse(
        ssml,
        card=card,
        should_end=True
    )


def help_intent(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    """
    This is triggered when the user asks for "help".

    :param intent:
    :param attributes:
    :return:
    """
    ssml = speechlet.SSML(
        '<speak>'
        '<s>Ok, Help.</s>'
        # Init options
        '<p>First, you can ask me for the workout, strength, or conditioning.</p>'
        
        # Yesterday/Tomorrow
        '<p>You can also add words like yesterday or tomorrow. '
        '<s>For example, ask me for yesterday’s workout or tomorrow’s conditioning.</s></p>'

        # DOW
        '<p>You can also include a day of the week. '
        '<s>For example, ask me for monday’s workout, or friday’s strength.</s></p>'

        # Quit
        '<p>Finally, you can say nevermind to quit.</p>'

        # Prompt
        '<s>What will it be?</s>'
        '</speak>'
    )
    card = speechlet.SimpleCard(
        title='Help',
        content=dedent(
            '''
            Example Phrases:
            
            "workout", "strength", "conditioning", "yesterday's workout", "tomorrow's conditioning",
            "monday's workout", "friday's strength", "nevermind".
            '''
        )
    )
    return speechlet.SpeechletResponse(
        ssml,
        card=card,
        should_end=False,
        attributes={
            'confirm_choice': True
        }
    )


def welcome_msg() -> speechlet.SpeechletResponse:
    """
    This is the basic welcome message when the user asks Alexa "Open Elliott Bay Crossfit".
    :return:
    """

    ssml = speechlet.SSML(
        '<speak>'
        '<s>Elliott Bay Crossfit.</s>'
        '<s>You can ask me for the workout, strength, or conditioning.</s>'
        '<s>You can also ask for help.</s>'
        '<s>Which will it be?</s>'
        '</speak>'
    )
    return speechlet.SpeechletResponse(
        ssml,
        card=speechlet.SimpleCard(
            title='Elliott Bay Crossfit',
            content='You can ask me for the "workout", "strength", or "conditioning".'
            ' You can also ask for "help". Which will it be?'
        ),
        should_end=False,
        attributes={
            'confirm_choice': True
        }
    )


def on_launch(request: dict, session: dict) -> speechlet.SpeechletResponse:
    LOG.debug('LAUNCH_REQUEST request_id=%s session_id=%s', request['requestId'], session['sessionId'])
    return welcome_msg()


INTENT_MODEL = {
    'QueryIntent': {
        'default': query_intent,
    },
    'AMAZON.HelpIntent': {
        'default': help_intent,
    },
    'AMAZON.CancelIntent': {
        'default': goodbye
    },
    'AMAZON.StopIntent': {
        'default': goodbye
    }
}


def on_intent(request: dict, session: dict) -> speechlet.SpeechletResponse:
    intent = request['intent']
    intent_name = request['intent']['name']
    LOG.debug('INTENT_REQUEST intent_name: %s request_id=%s session_id=%s',
              intent_name, request['requestId'], session['sessionId'])
    attributes = session.get('attributes', {})
    state = attributes.get('state', 'default')
    intent_handlers = INTENT_MODEL[intent_name]
    if state in intent_handlers:
        return intent_handlers[state](intent, attributes)
    return intent_handlers['default'](intent, attributes)


def on_session_end(request: dict, session: dict) -> speechlet.SpeechletResponse:
    LOG.debug('SESSION_ENDED_REQUEST request_id=%s session_id=%s', request['requestId'], session['sessionId'])
    return end_session()


REQUEST_HANDLERS = {
    'LaunchRequest': on_launch,
    'IntentRequest': on_intent,
    'SessionEndedRequest': on_session_end
}
