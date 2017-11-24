from _ebcf_alexa import interaction_model as im
from _ebcf_alexa.incoming_types import Intent
from _ebcf_alexa.speechlet import SpeechletResponse
from _ebcf_alexa.wods import WOD
from _ebcf_alexa import env
from datetime import datetime
import pytest
from unittest.mock import patch


@pytest.yield_fixture
def mock_now():
    d = datetime(2017, 11, 20, 12, tzinfo=env.UTC)
    with patch.object(env, 'now', return_value=d) as mocknow:
        yield mocknow


@pytest.fixture
def fakewod(mock_now):
    return WOD({
        'strength': 'strength here',
        'conditioning': 'its hard',
        'date': '2017-11-20T00:00:00.000Z',
        'publishDate': '2017-11-20T00:00:00.000Z'
    })


@pytest.fixture(params=['full workout', 'everything', 'both', 'wod', 'wad'])
def intent_with_synonym(request):
    return Intent({
        'name': 'DefaultQuery',
        'slots': {
            'RelativeTo': {
                'name': 'RelativeTo',
                'value': 'today\'s'
            },
            'RequestType': {
                'name': 'RequestType',
                'value': request.param
            }
        }
    })

PROMPT_FOR_SLOT_MSG = 'Did you want strength, conditioning, or both?'


class TestQueryIntent(object):
    def assert_response_is_reprompt(self,
                                    response: SpeechletResponse,
                                    expected_relative_to: str):
        assert PROMPT_FOR_SLOT_MSG in response.output_speech.ssml
        assert not response.should_end
        assert 'intents' in response.attributes
        intents = response.attributes['intents']
        assert 'DefaultQuery' in intents
        default_query = intents['DefaultQuery']
        assert 'RelativeTo' in default_query['slots']
        relative_to_slot = default_query['slots']['RelativeTo']
        assert relative_to_slot['value'] == expected_relative_to
        assert PROMPT_FOR_SLOT_MSG in response.reprompt.ssml

    def test_bad_RequestType_slot(self):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'today\'s'
                },
                'RequestType': {
                    'name': 'RequestType',
                    'value': 'strike'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_response_is_reprompt(response, 'today')

    def test_missing_RequestType_slot(self):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'today\'s'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_response_is_reprompt(response, 'today')

    def test_request_type_is_synonym(self, intent_with_synonym, fakewod):
        with patch('_ebcf_alexa.wods.get_wod', return_value=fakewod):
            response = im.query_intent(intent_with_synonym)
            assert 'strength here' in response.output_speech.ssml
            assert 'its hard' in response.output_speech.ssml
            assert not response.attributes
