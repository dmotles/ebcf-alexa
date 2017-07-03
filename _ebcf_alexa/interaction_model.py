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


ONEWEEK = timedelta(days=7)
ONEDAY = timedelta(days=1)


def _wod_speechlet(wod: wods.WOD, card_title: str) -> speechlet.SpeechletResponse:
    card_content = wod.pprint()
    if wod.image:
        card = speechlet.StandardCard(title=card_title, content=card_content, large_image_url=wod.image)
    else:
        card = speechlet.SimpleCard(title=card_title, content=card_content)
    return speechlet.SpeechletResponse(
        output_speech=speechlet.SSML(wod.speech_ssml()),
        card=card,
        should_end=True
    )


def _get_speech_date(d: Union[date, datetime]) -> str:
    return '{} {}, {}'.format(d.strftime('%A %B'), d.day, d.year)


def _get_full_date(d: date) -> str:
    now = env.date()
    if d == now+ONEDAY:
        return 'tomorrow, {}'.format(_get_speech_date(d))
    elif d == now-ONEDAY:
        return 'yesterday, {}'.format(_get_speech_date(d))
    elif d == now:
        return 'today, {}'.format(_get_speech_date(d))
    return _get_speech_date(d)


def get_todays_wod(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    now = env.localnow()
    today = now.date()
    start_time = now - ONEWEEK
    wod_list = wods.get_wods_by_range(start_time, now)
    wod_list.sort(key=attrgetter('date'), reverse=True)
    if wod_list:
        for wod in wod_list:
            if wod.date == today: # Times from ebcf are UTC but actually map to PST dates.
                return _wod_speechlet(wod, 'EBCF WOD for Today, {}'.format(_get_speech_date(today)))
        output = speechlet.PlainText('There is no WOD today, {}.'.format(_get_speech_date(today)))
        if wod_list[0].date == today-ONEDAY:
            output.text += ' Would you like to hear yesterday\'s?'
            reprompt = speechlet.PlainText('Would you like to hear yesterday\'s WOD?')
            card_title = 'EBCF WOD from Yesterday, {}'.format(_get_speech_date(wod_list[0].date))
        elif wod_list[0].date == today+ONEDAY:
            output.text += ' Tomorrow\'s has been posted. Would you like to hear it?'
            reprompt = speechlet.PlainText('Would you like to hear tomorrow\'s WOD?')
            card_title = 'EBCF WOD from Tomorrow, {}'.format(_get_speech_date(wod_list[0].date))
        else:
            return speechlet.SpeechletResponse(
                speechlet.PlainText(
                    'There was no WOD for today, yesterday, or tomorrow. '
                    'What day or date do your want the WOD for? You can also say cancel to exit.'
                ),
                reprompt=speechlet.PlainText(
                    'For day or date do your want the WOD for? You can also say cancel to exit.'
                ),
                should_end=False
            )
        return speechlet.SpeechletResponse(
            output_speech=output,
            reprompt=reprompt,
            should_end=False,
            attributes={
                'state': 'YES_NO_QUESTION_ASKED',
                'ifYes': {
                    'action': 'READ_WOD',
                    'card_title': card_title,
                    'wod': wod_list[0].as_wod_attributes()
                }
            }
        )
    return speechlet.SpeechletResponse(
        speechlet.PlainText(
            'I was unable to find any WODs. '
            'Give me a date for when you want the WOD, or say nevermind to exit.'
        ),
        reprompt='For when do you want the WOD? You can also say nevermind to exit',
        should_end=False
    )


def yes_answer(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    yes_attrs = attributes['ifYes']
    if yes_attrs['action'] == 'READ_WOD':
        card_title = yes_attrs['card_title']
        wod = wods.WOD(yes_attrs['wod'])
        return _wod_speechlet(wod, card_title)
    if yes_attrs['action'] == 'GET_TODAYS_WOD':
        return get_todays_wod(intent, attributes)
    raise ValueError('Unknown yes action - %s' % yes_attrs['action'])


def no_answer(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        speechlet.PlainText(
            'Ok. '
            'For what day do you want to know the WOD? You can also say "nevermind" to quit.'
        ),
        reprompt=speechlet.PlainText(
            'For what day do you want to know the WOD? You can also say "nevermind" to quit.'
        ),
        should_end=False
    )


def unknown_yes_no_answer(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        speechlet.PlainText(
            'I did not ask a yes or no question. '
            'For what day do you want to know the WOD? You can also say "nevermind" to quit.'
        ),
        reprompt=speechlet.PlainText(
            'For what day do you want to know the WOD? You can also say "nevermind" to quit.'
        ),
        should_end=False
    )


def goodbye(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    return end_session()


def end_session() -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        speechlet.PlainText('Goodbye.'),
        should_end=True
    )


def get_wod(intent: dict, attributes: dict) -> speechlet.SpeechletResponse:
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """
    try:
        date_str = intent['slots']['Date']['value']
    except KeyError:
        date_str = None

    if date_str:
        try:
            day = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = env.date()
            wod = wods.get_wod(day)
            when = _get_speech_date(day)
            iswas = 'is'
            if day > today:
                if day == today+ONEDAY:
                    when = 'tomorrow, ' + when
            elif day == today:
                when = 'today, ' + when
            else:
                iswas = 'was'
                if day == today-ONEDAY:
                    when = 'yesterday, ' + when

            if wod:
                if wod.publish_datetime and wod.publish_datetime <= env.now():
                    return _wod_speechlet(wod, 'EBCF WOD for {}'.format(_get_speech_date(wod.date)))
                return speechlet.SpeechletResponse(
                    speechlet.PlainText(
                        'The WOD for {} has not been posted yet. Try a different day. '
                        'For when do you want the WOD?'.format(when)
                    ),
                    reprompt=speechlet.PlainText('For when do you want the WOD?'),
                    should_end=False
                )
            else:
                return speechlet.SpeechletResponse(
                    speechlet.PlainText(
                        'There {} no WOD for {}. Try a different day. '
                        'For when do you want the WOD?'.format(iswas, when)
                    ),
                    reprompt=speechlet.PlainText('For when do you want the WOD?'),
                    should_end=False
                )
        except ValueError:
            pass
    return speechlet.SpeechletResponse(
        speechlet.PlainText('For which day?'),
        reprompt=speechlet.PlainText('For which day do you want the WOD? You can also say nevermind to exit.'),
        should_end=False
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
        should_end=False
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
        should_end=False
    )


def on_launch(request: dict, session: dict) -> speechlet.SpeechletResponse:
    LOG.debug('LAUNCH_REQUEST request_id=%s session_id=%s', request['requestId'], session['sessionId'])
    return welcome_msg()


INTENT_MODEL = {
    'GetTodaysWOD': {
        'default': get_todays_wod
    },
    'GetWOD': {
        'default': get_wod
    },
    'AMAZON.YesIntent': {
        'default': unknown_yes_no_answer,
        'YES_NO_QUESTION_ASKED': yes_answer
    },
    'AMAZON.NoIntent': {
        'default': unknown_yes_no_answer,
        'YES_NO_QUESTION_ASKED': no_answer
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
