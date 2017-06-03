"""
LAMBDA entry point
"""
from . import wods
from datetime import datetime, date

TODAY = date.today()


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(card_title, card_content, ssml, reprompt, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': ssml
        },
        'card': {
            'type': 'Simple',
            'title': card_title,
            'content': card_content
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    return build_response(
        session_attributes={},
        speechlet_response=build_speechlet_response(
            'Elliott Bay Crossfit',
            'HAY PEEPS',
            '<speak>Hello from <emphasis level="strong">Eliott Bay Crossfit</emphasis>. ' +
            'Ask me what\'s the WOD of the day!</speak>',
            'Ask me what\'s the WOD of the day, dude.',
            True
        )
    )


def handle_session_end_request():
    return build_response(
        session_attributes={},
        speechlet_response=build_speechlet_response(
            None,
            None,
            '<speak>Goodbye.</speak>',
            None,
            True
        )
    )


def get_wod(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """

    if 'Date' in intent['slots']:
        try:
            date_str = intent['slots']['Date']['value']
            print('Date from intent: %s' % date_str)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except KeyError:
            date = TODAY
    else:
        date = TODAY

    wod = wods.get_wod(date)
    if wod:
        ssml = wod.speech_ssml()
        print('SSML: %s' % ssml)
        return build_response(
            {},
            build_speechlet_response(
                'Elliott Bay Crossfit - WOD for %s' % date.isoformat(),
                wod.pprint(),
                ssml,
                'Ask me what is the wod for other days of the week, or what was the wod on a past day!',
                True
            )
        )
    return build_response(
        {},
        build_speechlet_response(
            'Elliott Bay Crossfit',
            'No WOD today...',
            '<speak>There\'s no WOD today. Ask me what\'s the WOD tomorrow, or what was the WOD yesterday, or what\'s the WOD on monday.</speak>',
            'Ask me what\'s the WOD tomorrow, yesterday, or Monday.',
            True
        )
    )


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
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

def lambda_handler(event, context):
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
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

