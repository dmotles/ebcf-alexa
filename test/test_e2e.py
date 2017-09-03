import pytest
from unittest.mock import NonCallableMagicMock, patch, mock_open, Mock
from _ebcf_alexa import wods, env
from ebcf_alexa import lambda_handler
from datetime import datetime


def patch_urlopen(response_str: str) -> Mock:
    """patch the API call for URLopen with a given response"""
    return patch.object(wods, 'urlopen', mock_open(read_data=response_str))


def assert_valid_response(resp: dict) -> None:
    assert resp['version'] == '1.0'
    assert 'response' in resp
    resp_inner = resp['response']
    if 'outputSpeech' in resp_inner:
        output_speech = resp_inner['outputSpeech']
        assert output_speech['type'] in ('PlainText', 'SSML')
        if output_speech['type'] == 'PlainText':
            assert 'text' in output_speech
        else:
            assert 'ssml' in output_speech
    assert 'shouldEndSession' in resp_inner


OPEN_SKILL = {'version': '1.0',
              'session': {'new': True, 'sessionId': 'amzn1.echo-api.session.4f9873cb-18e1-48e7-b078-180aba73e6b3',
                          'application': {'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'},
                          'user': {
                              'userId': 'amzn1.ask.account.XXXXX'}},
              'context': {'AudioPlayer': {'playerActivity': 'PLAYING'}, 'Display': {}, 'System': {
                  'application': {'applicationId': 'amzn1.ask.skill.d6f2f7c4-7689-410d-9c35-8f8baae37969'}, 'user': {
                      'userId': 'amzn1.ask.account.XXXXX'},
                  'device': {
                      'deviceId': 'amzn1.ask.device.XXXX',
                      'supportedInterfaces': {'AudioPlayer': {},
                                              'Display': {'templateVersion': '1.0', 'markupVersion': '1.0'},
                                              'VideoApp': {}}}, 'apiEndpoint': 'https://api.amazonalexa.com'}},
              'request': {'type': 'LaunchRequest',
                          'requestId': 'amzn1.echo-api.request.1552ecd8-907e-4308-8fd6-4710100120be',
                          'timestamp': '2017-09-03T18:34:11Z', 'locale': 'en-US'}}


EBCF_RESPONSE_WOD_20170901 = r"""
{"meta":{},"links":{"self":"http://www.elliottbaycrossfit.com/api/v1/wods?filter%5Bsimple%5D%5Bdate%5D=2017-09-01T00%3A00%3A00.000Z&filter%5Bsimple%5D%5Benabled%5D=true"},"data":[{"id":"599cb1c179707c0004b994ed","type":"wods","attributes":{"enabled":true,"title":null,"date":"2017-09-01T00:00:00.000Z","publishDate":"2017-09-01T04:00:00.000Z","image":"http://ebcf.s3.amazonaws.com/IMG_1910.JPG","strength":"HAPPY BIRTHDAY JACOB!!!!\nFront Squat \n3x2 @ 80% of 1RM","conditioning":"2 Minutes\n15 Push Ups, 50 Double Unders, Max Reps OH Squats 95#/75#\nRest 1 Minutes\n2 Minutes\n15 Push Ups, 50 Double Unders, Max Reps OH Squats 95#/75#\nRest 1 Minutes\n2 Minutes\n15 Push Ups, 50 Double Unders, Max Reps OH Squats 95#/75#\nRest 1 Minutes\n3 Minutes\n15 Push Ups, 50 Double Unders, Max Reps OH Squats 95#/75#\n\nWorkout is complete when you complete 75 OH Squats, if you don't complete 75 OH Squats within the given intervals, your score is total number of squats","description":null,"videoId":null},"links":{"self":"http://localhost:4500/api/v1/wods/599cb1c179707c0004b994ed"},"relationships":{"tags":{"data":[{"type":"tags","id":"56e61406e17eab8d035f2a42"},{"type":"tags","id":"59a49db56ca7ef0004dd7e2c"}],"links":{"self":"http://localhost:4500/api/v1/wods/relationships/tags"}}}}]}
""".strip()

EBCF_RESPONSE_WOD_20170901_SSML = '''
<speak><p>The workout for today, Friday September 1, 2017</p><p>Announcement:<s>HAPPY BIRTHDAY JACOB!!!!</s></p><p>Strength Section:</p><s>Front Squat</s><s>3 sets of 2 @ 80% of 1RM</s><p>Conditioning:</p><s>2 Minutes</s><s>15 Push Ups, 50 Double Unders, Max Reps <sub alias="overhead">OH</sub> Squats <prosody rate="fast">95<sub alias="pounds">#</sub> male, 75<sub alias="pounds">#</sub> female</prosody></s><s>Rest 1 Minutes</s><s>2 Minutes</s><s>15 Push Ups, 50 Double Unders, Max Reps <sub alias="overhead">OH</sub> Squats <prosody rate="fast">95<sub alias="pounds">#</sub> male, 75<sub alias="pounds">#</sub> female</prosody></s><s>Rest 1 Minutes</s><s>2 Minutes</s><s>15 Push Ups, 50 Double Unders, Max Reps <sub alias="overhead">OH</sub> Squats <prosody rate="fast">95<sub alias="pounds">#</sub> male, 75<sub alias="pounds">#</sub> female</prosody></s><s>Rest 1 Minutes</s><s>3 Minutes</s><s>15 Push Ups, 50 Double Unders, Max Reps <sub alias="overhead">OH</sub> Squats <prosody rate="fast">95<sub alias="pounds">#</sub> male, 75<sub alias="pounds">#</sub> female</prosody></s><s></s><s>Workout is complete when you complete 75 <sub alias="overhead">OH</sub> Squats, if you don't complete 75 <sub alias="overhead">OH</sub> Squats within the given intervals, your score is total number of squats</s></speak>
'''.strip()


DATE_20170901 = datetime(2017, 9, 1, 12, tzinfo=env.UTC)


def test_open_skill():
    with patch_urlopen(EBCF_RESPONSE_WOD_20170901) as mock_urlopen, \
             patch.object(env, 'now', return_value=DATE_20170901) as mock_now:
        resp = lambda_handler(OPEN_SKILL, NonCallableMagicMock(name='context'))
        assert mock_urlopen.called
        assert mock_now.called
        assert_valid_response(resp)
        assert EBCF_RESPONSE_WOD_20170901_SSML == resp['response']['outputSpeech']['ssml']


DEPRECATED_CODE_REQUEST = {
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

@pytest.mark.xfail(reason='we currently dont handle interaction model changes in code.')
def test_interaction_model_breaking_change():
    resp = lambda_handler(DEPRECATED_CODE_REQUEST, NonCallableMagicMock('context'))
    assert_valid_response(resp)
