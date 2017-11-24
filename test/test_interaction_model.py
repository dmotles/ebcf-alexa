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


@pytest.fixture
def intent_with_bad_slots():
    return Intent({
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
    def test_bad_slots(self, intent_with_bad_slots):
        response = im.query_intent(intent_with_bad_slots)
        assert PROMPT_FOR_SLOT_MSG in response.output_speech.ssml
        assert not response.should_end
        assert 'intents' in response.attributes
        assert 'DefaultQuery' in response.attributes['intents']
        assert 'RelativeTo' in response.attributes['intents']['DefaultQuery']['slots']
        assert response.attributes['intents']['DefaultQuery']['slots']['RelativeTo']['value'] == 'today'
        assert PROMPT_FOR_SLOT_MSG in response.reprompt.ssml

    def test_request_type_is_synonym(self, intent_with_synonym, fakewod):
        with patch('_ebcf_alexa.wods.get_wod', return_value=fakewod):
            response = im.query_intent(intent_with_synonym)
            assert 'strength here' in response.output_speech.ssml
            assert 'its hard' in response.output_speech.ssml
            assert not response.attributes
