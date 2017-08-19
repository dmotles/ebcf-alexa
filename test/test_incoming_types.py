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
