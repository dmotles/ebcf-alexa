"""
Interaction Model

This module basically maps out the response tree for the skill.
"""
from datetime import timedelta, datetime, date
from typing import Union, Optional, Dict, Tuple
from textwrap import dedent
from enum import Enum
import logging
from . import wods
from . import speechlet
from . import env
from .incoming_types import RequestTypes, LambdaEvent, Intent, Slot

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

DEFAULT_QUERY_INTENT = 'DefaultQuery'
REQUEST_SLOT = 'RequestType'
RELATIVE_SLOT = 'RelativeTo'


def _get_speech_date(d: Union[date, datetime]) -> str:
    return '{} {}, {}'.format(d.strftime('%A %B'), d.day, d.year)


def _titleify(word:str) -> str:
    return word[0].upper() + word[1:]


class RelativeTo(Enum):
    TODAY = (timedelta(), 'today')
    YESTERDAY = (timedelta(days=-1), 'yesterday')
    TOMORROW = (timedelta(days=1), 'tomorrow')

    def __init__(self, day_offset: timedelta, spoken_name: str):
        self.day_offset = day_offset
        self.spoken_name = spoken_name

    @property
    def title_name(self) -> str:
        return _titleify(self.spoken_name)


class RequestTypeSlot(Enum):
    FULL = ('workout', {
        'workout': 'workout',
        'wod': 'wod',
        'wad': 'wod',
        'both': 'full workout',
        'everything': 'full workout',
        'full': 'full workout'})
    STRENGTH = ('strength', {
        'strength': 'strength',
        'lifting': 'lifting'
    })
    CONDITIONING = ('conditioning', {
        'conditioning': 'conditioning',
        'metcon': 'metcon',
        'cardio': 'cardio',
        'endurance': 'endurance'})

    def __init__(self, default_spoken_word: str, synonyms: Dict[str, str]):
        self.default_spoken_word = default_spoken_word
        self.synonyms = synonyms


TEMPLATE_NO_THING = 'There {iswas} no {thing} {relative_to} {date}.'
TEMPLATE_FOUND = '<p>The {thing} for {relative_to}, {date}</p>{content}'
CARD_TITLE_TEMPLATE = '{thing} for {relative_to}, {date}'


def _build_wod_query_response(wod: Optional[wods.WOD],
                              wod_query_date: datetime,
                              relative_to: RelativeTo,
                              ebcf_slot_word: Optional[str],
                              request_type_slot: RequestTypeSlot) -> speechlet.SpeechletResponse:
    thing = ebcf_slot_word or request_type_slot.default_spoken_word
    speech_date = _get_speech_date(wod_query_date)
    card_cls = speechlet.SimpleCard
    if wod:
        if request_type_slot == RequestTypeSlot.FULL:
            ssml_txt = wod.full_ssml()
            card_content = wod.pprint()
            if wod.image:
                card_cls = lambda title, content: speechlet.StandardCard(title, content, wod.image)
        elif request_type_slot == RequestTypeSlot.STRENGTH:
            ssml_txt = wod.strength_ssml()
            card_content = wod.strength_pprint()
        elif request_type_slot == RequestTypeSlot.CONDITIONING:
            ssml_txt = wod.conditioning_ssml()
            card_content = wod.conditioning_pprint()
        else:
            assert False, 'Unknown EBCF section'
        if ssml_txt:
            return speechlet.SpeechletResponse(
                output_speech=speechlet.SSML(
                    TEMPLATE_FOUND.format(
                        thing=thing,
                        relative_to=relative_to.spoken_name,
                        date=speech_date,
                        content=ssml_txt
                    )
                ),
                card=card_cls(
                    title=CARD_TITLE_TEMPLATE.format(
                        thing=_titleify(thing),
                        relative_to=relative_to.title_name,
                        date=speech_date
                    ),
                    content=card_content
                ),
                should_end=True
            )
    iswas = 'is' if relative_to != RelativeTo.YESTERDAY else 'was'
    return speechlet.SpeechletResponse(
        output_speech=speechlet.PlainText(TEMPLATE_NO_THING.format(
            iswas=iswas,
            thing=thing,
            relative_to=relative_to.spoken_name,
            date=speech_date)
        ),
        should_end=True
    )


def wod_query(relative_to: RelativeTo=RelativeTo.TODAY,
              ebcf_slot_word: Optional[str]=None,
              request_type_slot: RequestTypeSlot=RequestTypeSlot.FULL) -> speechlet.SpeechletResponse:
    wod_query_date = env.localnow()
    if relative_to != RelativeTo.TODAY:
        wod_query_date += relative_to.day_offset
    wod = wods.get_wod(wod_query_date.date())
    return _build_wod_query_response(
        wod, wod_query_date, relative_to, ebcf_slot_word, request_type_slot
    )


def _get_relative_to_slot(slot: Slot) -> RelativeTo:
    LOG.debug('RelativeTo: %r', slot)
    if slot.has_value and slot.value:
        test_val = slot.value.lower()
        for rel in RelativeTo:
            if test_val.startswith(rel.spoken_name):
                slot.is_valid = True
                slot.value = rel.spoken_name
                return rel
    return RelativeTo.TODAY


def _resolve_request_type_slot(slot: Slot) -> Tuple[RequestTypeSlot, Optional[str]]:
    if slot.has_value and slot.value:
        test_val = slot.value.lower()
        for ebcfsec in RequestTypeSlot:
            if test_val in ebcfsec.synonyms:
                return ebcfsec, ebcfsec.synonyms[test_val]
            for syn in ebcfsec.synonyms:
                if test_val.startswith(syn):
                    return ebcfsec, ebcfsec.synonyms[syn]


def _get_request_type_slot(intent: Intent) -> Tuple[RequestTypeSlot, Optional[str]]:
    try:
        slot = intent.slots[REQUEST_SLOT]
    except KeyError:
        raise MissingSlot(REQUEST_SLOT)
    LOG.debug('RequestType: %r', slot)
    resolved = _resolve_request_type_slot(slot)
    if resolved is None and intent.last_intent is not None \
            and REQUEST_SLOT in intent.last_intent.slots:
        # Maybe we picked up a new value that was some garbage. Try old value.
        slot = intent.last_intent.slots[REQUEST_SLOT]
        LOG.debug('RequestType from last: %r', slot)
        resolved = _resolve_request_type_slot(slot)
    if resolved is not None:
        return resolved
    raise MissingSlot(REQUEST_SLOT)


def _prompt_missing_request_type_slot(intent: Intent) -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        output_speech=speechlet.SSML(
            'I didn\'t understand what you wanted. '
            'Did you want strength, conditioning, or both?'
        ),
        should_end=False,
        attributes={
            'intents': {
                intent.name: intent.to_dict()
            }
        },
        reprompt=speechlet.SSML(
            'Did you want strength, conditioning, or both?'
        )
    )


class MissingSlot(Exception):
    """raised when we don't know what section the user wanted, either
    because Alexa didn't hear it correctly or the user gave us some BS
    that we can't process.
    """


def query_intent(intent: Intent) -> speechlet.SpeechletResponse:
    """
    Responds to most queries of the skill.
    """
    relative_to = _get_relative_to_slot(intent.slots[RELATIVE_SLOT])
    try:
        request_type_slot, word_used = _get_request_type_slot(intent)
    except MissingSlot:
        return _prompt_missing_request_type_slot(intent)
    return wod_query(relative_to, word_used, request_type_slot)


HELP_SSML = (
    '<speak>'
    '<s>Ok, Help.</s>'
    # Init options
    '<p>First, you can ask me for the workout, strength, or conditioning.</p>'

    # Yesterday/Tomorrow
    '<p>You can also add words like: "yesterday", or, "tomorrow". '
    '<s>For example, ask me for yesterday’s workout or tomorrow’s conditioning.</s></p>'

    # Quit
    '<p>Finally, you can say: "exit", to quit.</p>'

    # Prompt
    '<s>What will it be?</s>'
    '</speak>')


def help_intent(intent: Intent) -> speechlet.SpeechletResponse:
    """
    This is triggered when the user asks for "help".

    :param intent:
    :param attributes:
    :return:
    """
    ssml = speechlet.SSML(HELP_SSML)
    card = speechlet.SimpleCard(
        title='Help',
        content=dedent(
            '''
            Example Phrases:

            "workout", "strength", "conditioning", "yesterday's workout", "tomorrow's conditioning".
            '''
        )
    )
    return speechlet.SpeechletResponse(
        ssml,
        card=card,
        should_end=False
    )


def cancel_intent(intent: Intent) -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(
        speechlet.PlainText('Goodbye.'),
        should_end=True
    )


_INTENTS = {
    DEFAULT_QUERY_INTENT: query_intent,
    'AMAZON.HelpIntent': help_intent,
    'AMAZON.CancelIntent': cancel_intent,
    'AMAZON.StopIntent': cancel_intent
}


class UnkownIntentException(Exception):
    def __init__(self, intent: Intent):
        super().__init__()
        self.intent = intent

    def __str__(self):
        return str(self.intent)


def on_intent_request(event: LambdaEvent) -> speechlet.SpeechletResponse:
    intent = event.request.intent
    intent_func = _INTENTS.get(intent.name, None)
    if not intent_func:
        LOG.error('UNKNOWN INTENT: %s', intent)
        raise UnkownIntentException(intent)
    return intent_func(intent)


def on_launch_request(event: LambdaEvent) -> speechlet.SpeechletResponse:
    return wod_query()


def on_session_end_request(event: LambdaEvent) -> speechlet.SpeechletResponse:
    return speechlet.SpeechletResponse(should_end=True)


class UnsupportedEventType(Exception):
    """raised when an unsupported event type comes in"""


def handle_event(event: LambdaEvent) -> speechlet.SpeechletResponse:
    request_type = event.request.type
    if request_type == RequestTypes.LaunchRequest:
        return on_launch_request(event)
    elif request_type == RequestTypes.IntentRequest:
        return on_intent_request(event)
    elif request_type == RequestTypes.SessionEndedRequest:
        return on_session_end_request(event)
    raise UnsupportedEventType(event)
