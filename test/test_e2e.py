import pytest
from unittest.mock import NonCallableMagicMock, Mock, patch, mock_open
from _ebcf_alexa import wods
from ebcf_alexa import lambda_handler

EBCF_WEBSITE_JSON = r"""
{"links":{"self":"http://www.elliottbaycrossfit.com/api/v1/wods?filter%5Bsimple%5D%5Bdate%5D=2017-06-01T00%3A00%3A00.000Z&filter%5Bsimple%5D%5Benabled%5D=True"},"data":[{"id":"591f33008961150004cbb9a0","type":"wods","attributes":{"enabled":true,"title":null,"date":"2017-06-02T00:00:00.000Z","publishDate":"2017-06-02T04:00:00.000Z","image":"http://ebcf.s3.amazonaws.com/6-1.jpg","strength":"Hang Power Snatch \n4x3\nDo not drop bar, work at moderate weight, focus on barbell cycling","conditioning":"30 Snatches 115#/95#\n30 Clean & Jerks 115#/95#\n30 Muscle Ups","description":null,"videoId":null},"links":{"self":"http://localhost:4500/api/v1/wods/591f33008961150004cbb9a0"},"relationships":{"tags":{"data":[{"type":"tags","id":"56e61406e17eab8d035f2a1e"},{"type":"tags","id":"56e61406e17eab8d035f2a74"},{"type":"tags","id":"56e61406e17eab8d035f2a4a"},{"type":"tags","id":"572e83adad8b7003006f9ede"},{"type":"tags","id":"591f32f88961150004cbb99f"}],"links":{"self":"http://localhost:4500/api/v1/wods/relationships/tags"}}}}]}
""".strip()


GET_WOD_EVENT = {
    "session": {
        "sessionId": "SessionId.dff1b708-2aeb-4d08-8fa8-aaf549836707",
        "application": {
            "applicationId": "amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969"
        },
        "attributes": {},
        "user": {
            "userId": "amzn1.ask.account.AGF7EUF4RNORLHSZDNU7KR7W75A2GRGQPT6OMHLBACZBLFKZTA2SPNW2UR527IFJRSPTPMMG5F2J64FH67DWLVUYNRDO5IOLQ2OSS22UJAMPG7YLDFDFSMMVQKWUIIIX5PI3RBDV4YGFZN6M5LR2GV52NQND5PJPVHVE3NAYGSGPLNNPDI6PYTKNAQMBJW2KLONN2Z7F77FUZPA"
        },
        "new": True
    },
    "request": {
        "type": "IntentRequest",
        "requestId": "EdwRequestId.64cef551-0040-4b50-967c-5a2698067cc2",
        "locale": "en-US",
        "timestamp": "2017-06-03T23:27:15Z",
        "intent": {
            "name": "GetWOD",
            "slots": {
                "Date": {
                    "name": "Date",
                    "value": "2017-06-02"
                }
            }
        }
    },
    "version": "1.0"
}

YES_INTENT_EVENT = {
  "session": {
    "sessionId": "SessionId.d52a4dc9-90fe-4d83-92e0-569ef47832d8",
    "application": {
      "applicationId": "amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969"
    },
    "attributes": {"date": "2017-06-02"},
    "user": {
      "userId": "amzn1.ask.account.AGF7EUF4RNORLHSZDNU7KR7W75A2GRGQPT6OMHLBACZBLFKZTA2SPNW2UR527IFJRSPTPMMG5F2J64FH67DWLVUYNRDO5IOLQ2OSS22UJAMPG7YLDFDFSMMVQKWUIIIX5PI3RBDV4YGFZN6M5LR2GV52NQND5PJPVHVE3NAYGSGPLNNPDI6PYTKNAQMBJW2KLONN2Z7F77FUZPA"
    },
    "new": False
  },
  "request": {
    "type": "IntentRequest",
    "requestId": "EdwRequestId.6c073620-a9db-4c8e-be8d-ab8d819a525a",
    "locale": "en-US",
    "timestamp": "2017-06-06T00:38:36Z",
    "intent": {
      "name": "AMAZON.YesIntent",
      "slots": {}
    }
  },
  "version": "1.0"
}

EXPECTED = {
  "version": "1.0",
  "response": {
    "outputSpeech": {
      "type": "SSML",
      "ssml": "<speak><p>Announcement: NO EVENING CLASSES TODAY</p><p>Strength Section:</p><s>Front Squat</s><s>4 sets of 4</s><s>Go up 5<sub alias=\"pounds\">#</sub> from last week</s><p>Conditioning:</p><s>15 Min AMRAP</s><s>30 Wall Balls 20<sub alias=\"pounds\">#</sub> male, 14<sub alias=\"pounds\">#</sub> female, 10<sub alias=\"feet\">'</sub> male, 9<sub alias=\"feet\">'</sub> female</s><s>30 Ring Dips</s><s>30 Pistols</s><s>30 <sub alias=\"dumbbell\">DB</sub> Clean and Jersks 50<sub alias=\"pounds\">#</sub> male, 35<sub alias=\"pounds\">#</sub> female</s></speak>"
    },
    "card": {
      "content": "Strength:\nNO EVENING CLASSES TODAY\n\nFront Squat\n4x4\nGo up 5# from last week\nConditioning:\n15 Min AMRAP\n30 Wall Balls 20#/14#, 10'/9'\n30 Ring Dips\n30 Pistols\n30 DB Clean & Jersks 50#/35#\nImage: None",
      "title": "Elliott Bay Crossfit - WOD for 2017-06-02",
      "type": "Simple"
    },
    "reprompt": {
      "outputSpeech": {
        "type": "PlainText",
        "text": "Ask me what is the wod for other days of the week, or what was the wod on a past day!"
      }
    },
    "shouldEndSession": True
  },
  "sessionAttributes": {}
}


@pytest.fixture(scope='module', params=[GET_WOD_EVENT, YES_INTENT_EVENT])
def lambda_response(request):
    with patch.object(wods, 'urlopen', mock_open(read_data=EBCF_WEBSITE_JSON)):
        return lambda_handler(request.param, NonCallableMagicMock())


def test_response_has_version(lambda_response):
    assert lambda_response['version'] == '1.0'


def test_response_has_sessionAttributes(lambda_response):
    assert lambda_response['sessionAttributes'] == {}


@pytest.fixture(scope='module', params=[
    lambda r: r['outputSpeech'],
    pytest.mark.xfail(lambda r: r['reprompt']['outputSpeech'], reason='No reprompt on success')
])
def output_speech(lambda_response, request):
    return request.param(lambda_response['response'])


def test_response_output_speech(output_speech):
    assert output_speech['type'] in ('SSML', 'PlainText')
    if output_speech['type'] == 'SSML':
        assert output_speech['ssml'].startswith('<speak>')
        assert output_speech['ssml'].endswith('</speak>')
    elif output_speech['type'] == 'PlainText':
        assert output_speech['text'].strip()

