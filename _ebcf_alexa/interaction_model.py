"""
Interaction Model

This module basically maps out the response tree for the skill.
"""
from datetime import timedelta, datetime, date
from operator import attrgetter
from typing import Union
from textwrap import dedent
from enum import Enum
import logging
from . import wods
from . import speechlet
from . import env

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class QueryType(Enum):
    WORKOUT = 1
    STRENGTH = 2
    CONDITIONING = 3

    @property
    def pname(self):
        return self.name[0] + self.name[1:].lower()


def _get_speech_date(d: Union[date, datetime]) -> str:
    return '{} {}, {}'.format(d.strftime('%A %B'), d.day, d.year)


def _confirm_choice(should_confirm: bool, relative_qualifier: str, query: QueryType) -> str:
    if should_confirm:
        if relative_qualifier:
            return '<p>OK, {}\'s {}</p>'.format(relative_qualifier, query.name.lower())
        return '<p>OK, {}.</p>'.format(query.name.lower())
    return ''


def _wod_ssml(wod: wods.WOD, query_type: QueryType) -> str:
    if query_type == QueryType.CONDITIONING:
        return wod.conditioning_ssml()
    elif query_type == QueryType.STRENGTH:
        return wod.strength_ssml()
    return wod.full_ssml()


def _wod_card(wod: wods.WOD, query_type: QueryType) -> speechlet.SimpleCard:
    card_title = '{} for {}'.format(query_type.pname, _get_speech_date(wod.date))
    if query_type == QueryType.STRENGTH:
        card_content = wod.strength_pprint()
    elif query_type == QueryType.CONDITIONING:
        card_content = wod.conditioning_pprint()
    else:
        card_content = wod.pprint()
    if wod.image and query_type == QueryType.WORKOUT: # full workout w/ announcement, show pic
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
        try:
            relative_qualifier = attributes['RelativeQualifier']
        except KeyError:
            relative_qualifier = None
    try:
        query_type = intent['slots']['Query']['value']
    except KeyError:
        try:
            query_type = attributes['Query']
        except KeyError:
            query_type = None
    target_date = env.localdate()
    if query_type:
        if 'strength' in query_type.lower():
            qt = QueryType.STRENGTH
        elif 'condition' in query_type.lower():
            qt = QueryType.CONDITIONING
        else:
            qt = QueryType.WORKOUT
        ssml_txt = '<speak>' + _confirm_choice(attributes.get('confirm_choice', False), relative_qualifier, qt)
        wod = wods.get_wod(target_date)
        if wod:
            if wod.publish_datetime < env.now():
                ssml_txt += _wod_ssml(wod, qt)
                card = _wod_card(wod, qt)
            else:
                ssml_txt += '<p>The wod for {} has not been posted yet.</p>'.format(_get_speech_date(wod.date))
                card = speechlet.SimpleCard(
                    title='{} for {}'.format(qt.pname, _get_speech_date(wod.date)),
                    content='Not posted yet.'
                )
        else:
            ssml_txt += '<p>No workout was found for {}</p>'.format(_get_speech_date(target_date))
            card = speechlet.SimpleCard(
                title='{} for {}'.format(qt.pname, _get_speech_date(target_date)),
                content='Not found.'
            )
        return speechlet.SpeechletResponse(
            speechlet.SSML(ssml_txt + '</speak>'),
            card=card,
            should_end=True
        )
    else:
        ssml_txt = 'You can say workout, strength, or conditioning. Which do you want?'
        if relative_qualifier:
            ssml_txt = 'I\'m not sure what you want for {}. '.format(relative_qualifier) + ssml_txt
        return speechlet.SpeechletResponse(
            speechlet.SSML(ssml_txt),
            should_end=False,
            attributes={
                'RelativeQualifier': relative_qualifier
            }
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
