import operator


class SlotsEquality(object):
    __slots__ = ()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.__slots__ == other.__slots__:
                attr_getters = [operator.attrgetter(attr)
                                for attr in self.__slots__]
                return all(getter(self) == getter(other)
                           for getter in attr_getters)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Event(SlotsEquality):
    """These events are returned by
    :obj:`Mpv.wait_event()<mpv.Mpv.wait_event()>`.

    Attributes:
        event_id (:obj:`mpv.EventID`): the event id.
        error (:obj:`mpv.ErrorCode`): This is mainly used for events that are
            replies to (asynchronous) requests.
        reply_userdata (): If the event is in reply to a request (made with
            this API and this API handle), this is set to the reply_userdata
            parameter of the request call. Otherwise, this field is 0.
        data (): The meaning and contents of the data member depend on the
            event_id.
            :obj:`Property <mpv.events.Property>`
            :obj:`LogMessage <mpv.events.LogMessage>`
            :obj:`ClientMessage <mpv.events.ClientMessage>`
            :obj:`EndFile <mpv.events.EndFile>`
            or ``None``

    """
    __slots__ = ('event_id', 'error', 'reply_userdata', 'data')

    def __init__(self, event_id, error, reply_userdata, data):
        self.event_id = event_id
        self.error = error
        self.reply_userdata = reply_userdata
        self.data = data


class Property(SlotsEquality):
    """The event data of a :obj:`PROPERTY_CHANGE <mpv.EventID>` event.

    Attributes:
        name (str): The name of the property.
        data (): Value of the property. The type is dependent on the property.

    """
    __slots__ = ('name', 'data')

    def __init__(self, name, data):
        self.name = name
        self.data = data

    def __repr__(self):
        return '<Property: ({}, {})>'.format(self.name, self.data)


class LogMessage(SlotsEquality):
    """The event data of a :obj:`LOG_MESSAGE <mpv.EventID>` event.

    Attributes:
        prefix (str): The module prefix, identifies the sender of the message.
        level (str): The log level as string.
        text (str): The log message.

    """
    __slots__ = ('prefix', 'level', 'text')

    def __init__(self, prefix, level, text):
        self.prefix = prefix
        self.level = level
        self.text = text


class ClientMessage(SlotsEquality):
    """The event data of a :obj:`CLIENT_MESSAGE <mpv.EventID>` event.

    Attributes:
        args (list): Arbitrary arguments chosen by the sender of the message.
            What these arguments mean is up to the sender and receiver.

    """
    __slots__ = ('args')

    def __init__(self, args):
        self.args = args


class EndFile(SlotsEquality):
    """The event data of a :obj:`END_FILE <mpv.EventID>` event.

    Attributes:
        reason (:obj:`mpv.EndFileReason`):
        error (:obj:`mpv.ErrorCode`):

    """
    __slots__ = ('reason', 'error')

    def __init__(self, reason, error):
        self.reason = reason
        self.error = error
