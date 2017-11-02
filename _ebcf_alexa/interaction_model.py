"""
Interaction Model

This module basically maps out the response tree for the skill.
"""
from datetime import timedelta, datetime, date
from typing import Union, Optional, Set, Tuple
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


class EBCFSection(Enum):
    FULL = ('workout', {'workout', 'wod', 'wad'})
    STRENGTH = ('strength', {'strength', 'lifting'})
    CONDITIONING = ('conditioning', {'conditioning', 'metcon', 'cardio', 'endurance'})

    def __init__(self, default_spoken_word: str, synonyms: Set[str]):
        self.default_spoken_word = default_spoken_word
        self.synonyms = synonyms


TEMPLATE_NO_THING = 'There {iswas} no {thing} {relative_to} {date}.'
TEMPLATE_FOUND = '<p>The {thing} for {relative_to}, {date}</p>{content}'
CARD_TITLE_TEMPLATE = '{thing} for {relative_to}, {date}'


def wod_query(relative_to: RelativeTo=RelativeTo.TODAY,
              ebcf_slot_word: Optional[str]=None,
              ebcf_section: EBCFSection=EBCFSection.FULL) -> speechlet.SpeechletResponse:
    wod_query_date = env.localnow()
    if relative_to != RelativeTo.TODAY:
        wod_query_date += relative_to.day_offset
    thing = ebcf_slot_word or ebcf_section.default_spoken_word
    speech_date = _get_speech_date(wod_query_date)
    wod = wods.get_wod(wod_query_date.date())
    card_cls = speechlet.SimpleCard
    if wod:
        if ebcf_section == EBCFSection.FULL:
            ssml_txt = wod.full_ssml()
            card_content = wod.pprint()
            if wod.image:
                card_cls = lambda title, content: speechlet.StandardCard(title, content, wod.image)
        elif ebcf_section == EBCFSection.STRENGTH:
            ssml_txt = wod.strength_ssml()
            card_content = wod.strength_pprint()
        elif ebcf_section == EBCFSection.CONDITIONING:
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


def _get_relative_to_slot(slot: Slot) -> RelativeTo:
    LOG.debug('RelativeTo: %r', slot)
    if slot.has_value and slot.value:
        test_val = slot.value.lower()
        for rel in RelativeTo:
            if test_val.startswith(rel.spoken_name):
                return rel
    return RelativeTo.TODAY


def _resolve_ebcf_section_slot(slot: Slot) -> Tuple[EBCFSection, Optional[str]]:
    if slot.has_value and slot.value:
        test_val = slot.value.lower()
        for ebcfsec in EBCFSection:
            if test_val in ebcfsec.synonyms:
                return ebcfsec, test_val
            for syn in ebcfsec.synonyms:
                if test_val.startswith(syn):
                    return ebcfsec, syn


def _get_ebcf_section_slot(intent: Intent) -> Tuple[EBCFSection, Optional[str]]:
    slot = intent.slots[REQUEST_SLOT]
    LOG.debug('RequestType: %r', slot)
    resolved = _resolve_ebcf_section_slot(slot)
    if resolved is None and intent.last_intent is not None \
            and REQUEST_SLOT in intent.last_intent.slots:
        # Maybe we picked up a new value that was some garbage. Try old value.
        slot = intent.last_intent.slots[REQUEST_SLOT]
        LOG.debug('RequestType from last: %r', slot)
        resolved = _resolve_ebcf_section_slot(slot)
    if resolved is not None:
        return resolved
    raise MissingEBCFSectionSlot(REQUEST_SLOT)


class MissingEBCFSectionSlot(Exception):
    """raised when we don't know what section the user wanted, either
    because Alexa didn't hear it correctly or the user gave us some BS
    that we can't process.
    """


def query_intent(intent: Intent) -> speechlet.SpeechletResponse:
    """
    Responds to most queries of the skill.
    """
    relative_to = _get_relative_to_slot(intent.slots[RELATIVE_SLOT])
    ebcf_section, word_used = _get_ebcf_section_slot(intent)
    return wod_query(relative_to, word_used, ebcf_section)


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
