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
      "userId": "amzn1.ask.account.AGF7EUF4RNORLHSZDNU7KR7W75A2GRGQPT6OMHLBACZBLFKZTA2SPNW2UR527IFJRSPTPMMG5F2J64FH67DWLVUYNRDO5IOLQ2OSS22UJAMPG7YLDFDFSMMVQKWUIIIX5PI3RBDV4YGFZN6M5LR2GV52NQND5PJPVHVE3NAYGSGPLNNPDI6PYTKNAQMBJW2KLONN2Z7F77FUZPA"
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
        "userId": "amzn1.ask.account.AGF7EUF4RNORLHSZDNU7KR7W75A2GRGQPT6OMHLBACZBLFKZTA2SPNW2UR527IFJRSPTPMMG5F2J64FH67DWLVUYNRDO5IOLQ2OSS22UJAMPG7YLDFDFSMMVQKWUIIIX5PI3RBDV4YGFZN6M5LR2GV52NQND5PJPVHVE3NAYGSGPLNNPDI6PYTKNAQMBJW2KLONN2Z7F77FUZPA"
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
    assert not req.session.new


VALID_LAUNCH_REQUEST_LAMBDA_EVENT = {
    'version': '1.0',
    'session': {
        'new': True,
        'sessionId': 'amzn1.echo-api.session.c1b6cfa8-e11d-4677-9431-0cab8e68315d',
        'application': {
            'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'},
        'user': {
            'userId': 'amzn1.ask.account.AGF7EUF4RNORLHSZDNU7KR7W75A2GRGQPT6OMHLBACZBLFKZTA2SPNW2UR527IFJRSPTPMMG5F2J64FH67DWLVUYNRDO5IOLQ2OSS22UJAMPG7YLDFDFSMMVQKWUIIIX5PI3RBDV4YGFZN6M5LR2GV52NQND5PJPVHVE3NAYGSGPLNNPDI6PYTKNAQMBJW2KLONN2Z7F77FUZPA'}},
    'context': {
        'AudioPlayer': {'playerActivity': 'STOPPED'}, 'Display': {},
        'System': {'application': {
            'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'},
            'user': {
                'userId': 'amzn1.ask.account.AGF7EUF4RNORLHSZDNU7KR7W75A2GRGQPT6OMHLBACZBLFKZTA2SPNW2UR527IFJRSPTPMMG5F2J64FH67DWLVUYNRDO5IOLQ2OSS22UJAMPG7YLDFDFSMMVQKWUIIIX5PI3RBDV4YGFZN6M5LR2GV52NQND5PJPVHVE3NAYGSGPLNNPDI6PYTKNAQMBJW2KLONN2Z7F77FUZPA'},
            'device': {
                'deviceId': 'amzn1.ask.device.AF3BKRU7L7QWY4SWLD23Q3EL6QL2CIFHXTWP3RLNAZS7UVCBQLDLLISPWSP744BPXUB5C2FMYK4NXKWORAQ73E4GVCMCWQXNCZ64EE7VNXAHIJDR5LXD3EC6CXBJK7UIMGO3PRBM3E22NJ7VWNU2GVZA5V7A',
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

