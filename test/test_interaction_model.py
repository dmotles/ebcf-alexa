from _ebcf_alexa import interaction_model as im
from _ebcf_alexa.incoming_types import Intent
import pytest

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


PROMPT_FOR_SLOT_MSG = 'Did you want the workout, strength, or conditioning?'


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
