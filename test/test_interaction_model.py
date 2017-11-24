from _ebcf_alexa import interaction_model as im
from _ebcf_alexa.incoming_types import Intent
from _ebcf_alexa.speechlet import SpeechletResponse
from _ebcf_alexa.wods import WOD
from _ebcf_alexa import env
from datetime import datetime
import pytest
from unittest.mock import patch


@pytest.yield_fixture(autouse=True)
def mock_now():
    d = datetime(2017, 11, 20, 12, tzinfo=env.UTC)
    with patch.object(env, 'now', return_value=d) as mocknow:
        yield mocknow


@pytest.yield_fixture(autouse=True)
def fakewod(mock_now):
    wod = WOD({
        'strength': 'strength section goes here',
        'conditioning': 'conditioning section goes here',
        'date': '2017-11-20T00:00:00.000Z',
        'publishDate': '2017-11-20T00:00:00.000Z'
    })
    with patch('_ebcf_alexa.wods.get_wod', return_value=wod) as mock:
        yield mock


PROMPT_FOR_SLOT_MSG = 'Did you want strength, conditioning, or both?'


class TestQueryIntentReprompt(object):
    @staticmethod
    def assert_response_is_reprompt(response: SpeechletResponse):
        assert PROMPT_FOR_SLOT_MSG in response.output_speech.ssml
        assert not response.should_end
        assert 'intents' in response.attributes
        intents = response.attributes['intents']
        assert 'DefaultQuery' in intents
        assert PROMPT_FOR_SLOT_MSG in response.reprompt.ssml

    @staticmethod
    def assert_relative_to_saved_in_attributes(response: SpeechletResponse,
                                               expected_value: str):
        relative_to_slot = response.attributes['intents']['DefaultQuery']['slots']['RelativeTo']
        assert relative_to_slot['value'] == expected_value

    @staticmethod
    def assert_request_type_saved_in_attributes(response: SpeechletResponse,
                                                expected_value: str):
        request_type_slot = response.attributes['intents']['DefaultQuery']['slots']['RequestType']
        assert request_type_slot['value'] == expected_value

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
        self.assert_response_is_reprompt(response)
        self.assert_relative_to_saved_in_attributes(response, 'today')

    def test_empty_RequestType_slot(self):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'today\'s'
                },
                'RequestType': {
                    'name': 'RequestType'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_response_is_reprompt(response)
        self.assert_relative_to_saved_in_attributes(response, 'today')

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
        self.assert_response_is_reprompt(response)
        self.assert_relative_to_saved_in_attributes(response, 'today')

    @pytest.mark.xfail(reason='Not implemented yet')
    def test_invalid_RelativeTo_slot(self):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'year\'s'
                },
                'RequestType': {
                    'name': 'RequestType',
                    'value': 'workout'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_response_is_reprompt(response)
        self.assert_request_type_saved_in_attributes(response, 'workout')

class TestQueryIntentWithPatchedOutGetWOD(object):
    @staticmethod
    def assert_opening_sentence_correct(response: SpeechletResponse,
                                        expected_request_type_word: str):
        expected_opening_sentence = (
            'The {expected} for today, Monday November 20, 2017'.format(
                expected=expected_request_type_word
            )
        )
        response_ssml = response.output_speech.ssml
        assert expected_opening_sentence in response_ssml

    @staticmethod
    def assert_is_full_workout(response: SpeechletResponse):
        response_ssml = response.output_speech.ssml
        assert 'strength section goes here' in response_ssml
        assert 'conditioning section goes here' in response_ssml

    @staticmethod
    def assert_strength_only(response: SpeechletResponse):
        response_ssml = response.output_speech.ssml
        assert 'strength section goes here' in response_ssml
        assert 'conditioning section goes here' not in response_ssml

    @staticmethod
    def assert_conditioning_only(response: SpeechletResponse):
        response_ssml = response.output_speech.ssml
        assert 'strength section goes here' not in response_ssml
        assert 'conditioning section goes here' in response_ssml

    @pytest.mark.parametrize('request_type,expected_thing', [
        ('workout', 'workout'),
        ('full workout', 'full workout'),
        ('wad', 'wod')
    ])
    def test_request_type_is_RequestTypeSlot_FULL(self, request_type, expected_thing):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'today\'s'
                },
                'RequestType': {
                    'name': 'RequestType',
                    'value': request_type
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_opening_sentence_correct(response, expected_thing)
        self.assert_is_full_workout(response)
        assert not response.attributes
        assert response.should_end

    def test_request_type_is_RequestTypeSlot_STRENGTH(self):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'today\'s'
                },
                'RequestType': {
                    'name': 'RequestType',
                    'value': 'strength'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_opening_sentence_correct(response, 'strength')
        self.assert_strength_only(response)
        assert not response.attributes
        assert response.should_end

    @pytest.mark.parametrize('request_type,expected_thing', [
        ('cardio', 'cardio'),
        ('conditioning', 'conditioning'),
        ('metcon', 'metcon')
    ])
    def test_request_type_is_RequestTypeSlot_CONDITIONING(self, request_type, expected_thing):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                    'value': 'today\'s'
                },
                'RequestType': {
                    'name': 'RequestType',
                    'value': request_type
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_opening_sentence_correct(response, expected_thing)
        self.assert_conditioning_only(response)
        assert not response.attributes
        assert response.should_end

    def test_empty_RelativeTo_slot(self):
        """Assuming RelativeTo empty means the user intended to get today's workout"""
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RelativeTo': {
                    'name': 'RelativeTo',
                },
                'RequestType': {
                    'name': 'RequestType',
                    'value': 'workout'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_opening_sentence_correct(response, 'workout')
        self.assert_is_full_workout(response)
        assert not response.attributes
        assert response.should_end

    def test_missing_RelativeTo_slot(self):
        intent = Intent({
            'name': 'DefaultQuery',
            'slots': {
                'RequestType': {
                    'name': 'RequestType',
                    'value': 'workout'
                }
            }
        })
        response = im.query_intent(intent)
        self.assert_opening_sentence_correct(response, 'workout')
        self.assert_is_full_workout(response)
        assert not response.attributes
        assert response.should_end
