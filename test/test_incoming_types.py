from _ebcf_alexa import incoming_types

VALID_INTENT_LAMBDA_EVENT = {
  "session": {
    "new": False,
    "sessionId": "SessionId.10809a6f-e431-42f6-8d02-1d71ffab2251",
    "application": {
      "applicationId": "amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969"
    },
    "attributes": {},
    "user": {
      "userId": "amzn1.ask.account.XXXXX"
    }
  },
  "request": {
    "type": "IntentRequest",
    "requestId": "EdwRequestId.eb6a8e40-8272-4d2b-ad2c-d9b7cc787a67",
    "intent": {
      "name": "DefaultQuery",
      "slots": {
        "RelativeTo": {
          "name": "RelativeTo"
        }
      }
    },
    "locale": "en-US",
    "timestamp": "2017-08-19T19:04:26Z"
  },
  "context": {
    "AudioPlayer": {
      "playerActivity": "IDLE"
    },
    "System": {
      "application": {
        "applicationId": "amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969"
      },
      "user": {
        "userId": "amzn1.ask.account.XXXXX"
      },
      "device": {
        "supportedInterfaces": {}
      }
    }
  },
  "version": "1.0"
}


def test_intent_request():
    req = incoming_types.LambdaEvent(VALID_INTENT_LAMBDA_EVENT)
    assert req.session.application.application_id == "amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969"
    assert req.request.type == incoming_types.RequestTypes.IntentRequest
    assert req.request.intent.name == 'DefaultQuery'
    assert req.request.intent.slots['RelativeTo'].name == 'RelativeTo'
    assert not req.request.intent.slots['RelativeTo'].has_value
    assert repr(req.request.intent.slots['RelativeTo']) # test that this returns a non-empty string...
    assert not req.session.new


VALID_LAUNCH_REQUEST_LAMBDA_EVENT = {
    'version': '1.0',
    'session': {
        'new': True,
        'sessionId': 'amzn1.echo-api.session.c1b6cfa8-e11d-4677-9431-0cab8e68315d',
        'application': {
            'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'},
        'user': {
            'userId': 'amzn1.ask.account.XXXXX'}},
    'context': {
        'AudioPlayer': {'playerActivity': 'STOPPED'}, 'Display': {},
        'System': {'application': {
            'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'},
            'user': {
                'userId': 'amzn1.ask.account.XXXXXX'},
            'device': {
                'deviceId': 'amzn1.ask.device.XXXXX',
                'supportedInterfaces': {'AudioPlayer': {}, 'Display': {
                    'templateVersion': '1.0', 'markupVersion': '1.0'},
                                        'VideoApp': {}}},
            'apiEndpoint': 'https://api.amazonalexa.com'}},
    'request': {'type': 'LaunchRequest',
                'requestId': 'amzn1.echo-api.request.0f045029-0f67-4a4f-9ccd-a0e7822b789d',
                'timestamp': '2017-08-19T19:58:27Z', 'locale': 'en-US'}}


def test_launch_request():
    req = incoming_types.LambdaEvent(VALID_LAUNCH_REQUEST_LAMBDA_EVENT)
    assert req.session.application.application_id == "amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969"
    assert req.request.type == incoming_types.RequestTypes.LaunchRequest
    assert req.session.new


VALID_CANCEL_INTENT_EVENT = {
    'version': '1.0',
    'session': {'new': False, 'sessionId': 'amzn1.echo-api.session.3fea2408-d1ed-44b2-8343-42106601e585',
                'application': {'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'}, 'user': {
            'userId': 'amzn1.ask.account.XXXXXX'}},
    'context': {'AudioPlayer': {'playerActivity': 'STOPPED'}, 'Display': {'token': ''},
                'System': {'application': {'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'},
                           'user': {
                               'userId': 'amzn1.ask.account.XXXXXX'},
                           'device': {
                               'deviceId': 'amzn1.ask.device.XXXXXXX',
                               'supportedInterfaces': {'AudioPlayer': {},
                                                       'Display': {'templateVersion': '1.0', 'markupVersion': '1.0'},
                                                       'VideoApp': {}}}, 'apiEndpoint': 'https://api.amazonalexa.com'}},
    'request': {'type': 'IntentRequest', 'requestId': 'amzn1.echo-api.request.6cdc55fe-d1be-46bc-b315-0f1a779a24b6',
                'timestamp': '2017-08-19T20:08:35Z', 'locale': 'en-US',
                'intent': {'name': 'AMAZON.CancelIntent', 'confirmationStatus': 'NONE'}}}


def test_cancel_intent():
    req = incoming_types.LambdaEvent(VALID_CANCEL_INTENT_EVENT)
    assert req.request.intent.name == 'AMAZON.CancelIntent'
    str(req.request) # does not crash
