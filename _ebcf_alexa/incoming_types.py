"""
Incoming lambda request objectifying
"""
import logging
from typing import Dict, Optional, Type
from enum import Enum, auto

LOG = logging.getLogger(__name__)
SUPPORTED_SCHEMA_VERSION = '1.0'


class _RequestApplication(object):
    application_id: str
    """A string representing the appliation ID for your skill."""

    def __init__(self, a: dict):
        self.application_id = a['applicationId']


class _RequestUser(object):
    user_id: str
    """
    A string that represents a unique identifier for the user who made the request. The length of this identifier
    can vary, but is never more than 255 characters. The userId is automatically generated when a user enables the
    skill in the Alexa app.  Note: Disabling and re-enabling a skill generates a new identifier."""

    def __init__(self, u: dict):
        self.user_id = u['userId']


class _RequestSession(object):
    """Standard request types (LaunchRequest, IntentRequest, and SessionEndedRequest) include the session object."""

    new: bool
    """
    A boolean value indicating whether this is a new session.
    Returns true for a new session or false for an existing session.
    """

    session_id: str
    """A string that represents a unique identifier per a user’s active session."""

    attributes: Optional[Dict[str, dict]] = None
    """A map of key-value pairs. The attributes map is empty for requests where a
    new session has started with the property new set to true."""

    application: _RequestApplication
    """An object containing an application ID.
    This is used to verify that the request was intended for your service.

    This information is also available in the context.System.application property."""

    user: _RequestUser
    """An object that describes the user making the request."""

    def __init__(self, s: dict):
        """
        :param s: session as dictionary
        """
        self.new = s['new']
        self.session_id = s['sessionId']
        self.attributes = s.get('attributes')
        self.application = _RequestApplication(s['application'])
        self.user = _RequestUser(s['user'])


class _RequestContextSystem(object):
    class Device(object):
        device_id: Optional[str]
        supported_interfaces: Dict[str, Dict]

        def __init__(self, d: dict):
            self.device_id = d.get('deviceId')
            self.supported_interfaces = d.get('supportedInterfaces', {})

    application: _RequestApplication
    user: _RequestUser
    device: Device
    api_endpoint: Optional[dict] = None

    def __init__(self, s: dict):
        self.application = _RequestApplication(s['application'])
        self.user = _RequestUser(s['user'])
        self.device = self.Device(s['device'])
        self.api_endpoint = s.get('apiEndpoint')


class _RequestContext(object):
    class AudioPlayer(object):
        token: Optional[str] = None
        offset_ms: Optional[int] = None
        activity: str

        def __init__(self, p:dict):
            self.token = p.get('token')
            self.offset_ms = p.get('offsetInMilliseconds')
            self.activity = p['playerActivity']

    system: _RequestContextSystem
    audio_player: AudioPlayer

    def __init__(self, c: dict):
        self.system = _RequestContextSystem(c['System'])

        # FireTV requests dont seem to have AudioPlayer
        # But Original Echo and Echo Show Do.
        self.audio_player = self.AudioPlayer(c.get('AudioPlayer', {}))


class _BaseAlexaRequest(object):
    """
    Base class for all Alexa Request Types
    """
    type = None # type: RequestTypes
    locale: str
    request_id: str
    timestamp: str

    def __init__(self, r: dict):
        self.locale = r['locale']
        self.request_id = r['requestId']
        self.timestamp = r['timestamp']

    def __repr__(self):
        return '<{} type={}>'.format(self.__class__.__name__, self.type)


class _AlexaLaunchRequest(_BaseAlexaRequest):
    """A LaunchRequest is an object that represents that a user made a request to an Alexa skill,
    but did not provide a specific intent."""
    def __init__(self, r: dict):
        super().__init__(r)
        self.type = RequestTypes.LaunchRequest


class Slot(object):
    name: str
    has_value: bool
    value: Optional[str]

    def __init__(self, s:dict):
        self.name = s['name']
        self.has_value = 'value' in s
        self.value = s.get('value')

    def __repr__(self):
        return '<{} {}={}>'.format(self.__class__.__name__, self.name, self.value)

    def __str__(self):
        if not self.value:
            if self.has_value:
                return repr(self.value)
            return '<NOT_SET>'
        return self.value


class Intent(object):
    name: str

    slots: Optional[Dict[str, Slot]] = None
    """
    A map of key-value pairs that further describes what the user meant based on a predefined intent schema.
    The map can be empty.
    """

    def __init__(self, i: dict):
        self.name = i['name']
        if 'slots' in i:
            self.slots = {
                k: Slot(v)
                for k, v in i['slots'].items()
            }

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.name)

    def __str__(self):
        slotstr = ''
        if self.slots:
            slotstr = ', '.join(
                '{}={}'.format(slot_name, slot)
                for slot_name, slot in self.slots.items())
        return '{}({})'.format(self.name, slotstr)


class _AlexaIntentRequest(_BaseAlexaRequest):
    """An IntentRequest is an object that represents a request made to a skill based on what the user wants to do."""

    intent: Intent
    """An object that represents what the user wants"""

    def __init__(self, r: dict):
        super().__init__(r)
        self.type = RequestTypes.IntentRequest
        self.intent = Intent(r['intent'])

    def __repr__(self):
        return '<{} type={} intent={}>'.format(self.__class__.__name__, self.type, self.intent)

    def __str__(self):
        return 'Intent: %s' % self.intent


class _AlexaSessionEndedRequest(_BaseAlexaRequest):
    """
    A SessionEndedRequest is an object that represents a request made to an Alexa skill to notify that a session was
    ended. Your service receives a SessionEndedRequest when a currently open session is closed for one of the
    following reasons:

    - The user says “exit”.
    - The user does not respond or says something that does not match an intent defined in your voice interface
      while the device is listening for the user’s response.
    - An error occurs.
    """

    class SessionEndError(object):
        type: str
        """
        a string indicating the type of error that occurred (INVALID_RESPONSE, DEVICE_COMMUNICATION_ERROR,
        INTERNAL_ERROR).
        """

        msg: Optional[str]
        """a string providing more information about the error. """

        def __init__(self, e: dict):
            self.type = e['type']
            self.msg = e.get('message')

        def __repr__(self):
            return '<{} "{}">'.format(self.__class__.__name__, self.type)

        def __str__(self):
            return '{}: {}'.format(self.type, self.msg)

    reason: str
    """
    Describes why the session ended. Possible values:

    - USER_INITIATED: The user explicitly ended the session.
    - ERROR: An error occurred that caused the session to end.
    - EXCEEDED_MAX_REPROMPTS: The user either did not respond or responded with an utterance that did not match
      any of the intents defined in your voice interface.
    """

    error: Optional[SessionEndError] = None
    """An error object providing more information about the error that occurred."""

    def __init__(self, r: dict):
        super().__init__(r)
        self.type = RequestTypes.SessionEndedRequest
        self.reason = r['reason']
        if 'error' in r:
            self.error = self.SessionEndError(r['error'])
        LOG.debug('SESSION_END reason: "%s", error: %s', self.reason, self.error)


class RequestTypes(Enum):
    LaunchRequest = (_AlexaLaunchRequest,)
    IntentRequest = (_AlexaIntentRequest,)
    SessionEndedRequest = (_AlexaSessionEndedRequest,)

    def __init__(self, cls_type: Type[_BaseAlexaRequest]):
        self.cls_type = cls_type

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


def _build_alexa_request(request: dict) -> _BaseAlexaRequest:
    req_type = RequestTypes[request['type']]
    LOG.debug('Request Type: %s', req_type)
    return req_type.cls_type(request)


class LambdaEvent(object):
    """
    All requests include the version, context, and request objects at the top level.
    The session object is included for all standard requests, but it is not included
    for AudioPlayer, VideoApp, or PlaybackController requests."""

    version: str
    """The version specifier for the request with the value defined as: 1.0"""

    session: Optional[_RequestSession] = None
    """The session object provides additional context associated with the request."""

    context: Optional[_RequestContext] = None
    """
    The context object provides your skill with information about the current state of the Alexa
    service and device at the time the request is sent to your service.
    This is included on all requests. For requests sent in the context of a session
    (LaunchRequest and IntentRequest), the context object duplicates the user and
    application information that is also available in the session."""

    request: _BaseAlexaRequest
    """A request object that provides the details of the user’s request.
    There are several different request types available."""

    def __init__(self, e: dict):
        self.version = e['version']
        LOG.debug('Request version: %s', self.version)
        assert self.version == SUPPORTED_SCHEMA_VERSION
        if e['session']:
            self.session = _RequestSession(e['session'])
        if 'context' in e:
            self.context = _RequestContext(e['context'])
        self.request = _build_alexa_request(e['request'])
