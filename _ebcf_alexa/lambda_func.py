"""
LAMBDA entry point
"""
from . import wods
from . import speechlet
from datetime import datetime, date, timedelta

TODAY = date.today()
ONEDAY = timedelta(days=1)

# Common phrases

WOD_PROMPT = """
For when do you want the wod for? You can say "yesterday", "today", "tomorrow", "last monday", or give me a specific date.
You can also say "nevermind" to quit.
""".strip()

WOD_PROMPT_SPEECHLET = speechlet.PlainText(WOD_PROMPT)


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response() -> speechlet.SpeechletResponse:
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    return speechlet.SpeechletResponse(
        output_speech=speechlet.PlainText('Would you like to know the workout today?'),
        reprompt=speechlet.PlainText('Would you like to know the workout today?'),
        should_end=False
    )


def handle_session_end_request() -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        output_speech=speechlet.PlainText('Goodbye.'),
        should_end=True
    )


def _get_day_text(date_: date) -> str:
    if date_ == TODAY:
        return 'Today'
    elif date_ == TODAY + ONEDAY:
        return 'Tomorrow'
    elif date_ == TODAY - ONEDAY:
        return 'Yesterday'
    return '{} {}, {}'.format(date_.strftime('%A %B'), date_.day, date_.year)


def _get_speech_for_no_wod(date_: date) -> str:
    if date_ == TODAY:
        return 'There is no wod today.'
    elif date_ == TODAY + ONEDAY:
        return 'There is no wod tomorrow.'
    elif date_ == TODAY - ONEDAY:
        return 'There was no wod yesterday.'
    date_text = '{} {}, {}.'.format(date_.strftime('%A %B'), date_.day, date_.year)
    if date_ > TODAY:
        return 'There is no wod on ' + date_text
    return 'There was no wod on ' + date_text


def get_wod(intent: dict, session: dict) -> speechlet.SpeechletResponse:
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """
    if 'Date' in intent['slots']:
        try:
            date_str = intent['slots']['Date']['value']
            print('Date from intent: %s' % date_str)
            if not date_str:
                return speechlet.SpeechletResponse(
                    output_speech=WOD_PROMPT_SPEECHLET,
                    reprompt=WOD_PROMPT_SPEECHLET,
                    should_end=False
                )
            date_ = datetime.strptime(date_str, '%Y-%m-%d').date()
        except KeyError:
            date_ = TODAY
    else:
        date_ = TODAY

    wod = wods.get_wod(date_)
    if wod:
        ssml = wod.speech_ssml()
        return speechlet.SpeechletResponse(
            output_speech=speechlet.SSML(wod.speech_ssml()),
            card=speechlet.SimpleCard(
                title='EBCF WOD for {}'.format(_get_day_text(date_)),
                content=wod.pprint()
            )
        )
    return speechlet.SpeechletResponse(
        output_speech=speechlet.PlainText(
            _get_speech_for_no_wod(date_) + ' ' + WOD_PROMPT
        ),
        reprompt=WOD_PROMPT_SPEECHLET,
        should_end=False
    )

# --------------- Events ------------------

def on_session_started(session_started_request: dict, session: dict) -> None:
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request: dict, session: dict) -> speechlet.SpeechletResponse:
    """ Called when the user launches the skill without specifying what they
    want
    """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request: dict, session: dict) -> speechlet.SpeechletResponse:
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetWOD":
        return get_wod(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context) -> dict:
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session']).dict()
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session']).dict()
    elif event['request']['type'] == "SessionEndedRequest":
        on_session_ended(event['request'], event['session'])
        return handle_session_end_request().dict()
    raise ValueError('Unknown request type.')

