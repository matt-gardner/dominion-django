"""
I (Matt Gardner) found this code on the internet at this location on 11/26/2011:

https://github.com/mtah/python-websocket

It originally had the GPL license statement at the top of the file; I am
leaving that license statement intact at the end of this doc string.

I have modified the code slightly to make it more amenable to my needs.  Those
modifications are as follows:

11/26/2011: Pass the websocket object to the handler methods, so that a message
can more easily trigger a response.
11/26/2011: Made the client speak the socket.io protocol, as that's what the
server I'm using speaks.

LICENSE:

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import sys, re, urlparse, socket, asyncore, simplejson

MSG_FRAME = "~m~"
HEARTBEAT_FRAME = "~h~"
JSON_FRAME = "~j~"

class WebSocket(object):
    def __init__(self, url, **kwargs):
        self.host, self.port, self.resource, self.secure = WebSocket._parse_url(url)
        self.protocol = kwargs.pop('protocol', None)
        self.cookie_jar = kwargs.pop('cookie_jar', None)
        self.onopen = kwargs.pop('onopen', None)
        self.onmessage = kwargs.pop('onmessage', None)
        self.onerror = kwargs.pop('onerror', None)
        self.onclose = kwargs.pop('onclose', None)
        if kwargs: raise ValueError('Unexpected argument(s): %s' % ', '.join(kwargs.values()))

        self._dispatcher = _Dispatcher(self)

    def send(self, data):
        self._dispatcher.write('\x00' + encode_for_socketio(data) + '\xff')

    def close(self):
        self._dispatcher.handle_close()

    @classmethod
    def _parse_url(cls, url):
        p = urlparse.urlparse(url)

        if p.hostname:
            host = p.hostname
        else:
            raise ValueError('URL must be absolute')

        if p.fragment:
            raise ValueError('URL must not contain a fragment component')

        if p.scheme == 'ws':
            secure = False
            port = p.port or 80
        elif p.scheme == 'wss':
            raise NotImplementedError('Secure WebSocket not yet supported')
            # secure = True
            # port = p.port or 443
        else:
            raise ValueError('Invalid URL scheme')

        resource = p.path or u'/'
        if p.query: resource += u'?' + p.query
        return (host, port, resource, secure)

    #@classmethod
    #def _generate_key(cls):
    #    spaces = random.randint(1, 12)
    #    number = random.randint(0, 0xffffffff/spaces)
    #    key = list(str(number*spaces))
    #    chars = map(unichr, range(0x21, 0x2f) + range(0x3a, 0x7e))
    #    random_inserts = random.sample(xrange(len(key)), random.randint(1,12))
    #    for (i, c) in [(r, random.choice(chars)) for r in random_inserts]:
    #        key.insert(i, c)
    #    print key
    #    return ''.join(key)

class WebSocketError(Exception):
    def _init_(self, value):
        self.value = value

    def _str_(self):
        return str(self.value)

class _Dispatcher(asyncore.dispatcher):
    def __init__(self, ws):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((ws.host, ws.port))

        self.ws = ws
        self._read_buffer = ''
        self._write_buffer = ''
        self._handshake_complete = False

        if self.ws.port != 80:
            hostport = '%s:%d' % (self.ws.host, self.ws.port)
        else:
            hostport = self.ws.host

        fields = [
            'Upgrade: WebSocket',
            'Connection: Upgrade',
            'Host: ' + hostport,
            'Origin: http://' + hostport,
            #'Sec-WebSocket-Key1: %s' % WebSocket.generate_key(),
            #'Sec-WebSocket-Key2: %s' % WebSocket.generate_key()
        ]
        if self.ws.protocol: fields['Sec-WebSocket-Protocol'] = self.ws.protocol
        if self.ws.cookie_jar:
            cookies = filter(lambda c: _cookie_for_domain(c, _eff_host(self.ws.host)) and \
                             _cookie_for_path(c, self.ws.resource) and \
                             not c.is_expired(), self.ws.cookie_jar)

            for cookie in cookies:
                fields.append('Cookie: %s=%s' % (cookie.name, cookie.value))

        # key3 = ''.join(map(unichr, (random.randrange(256) for i in xrange(8))))
        self.write(encode_for_socketio('GET %s HTTP/1.1\r\n' \
                         '%s\r\n\r\n' % (self.ws.resource,
                                         '\r\n'.join(fields))))
                                         # key3)))

    def handl_expt(self):
        self.handle_error()

    def handle_error(self):
        self.close()
        t, e, trace = sys.exc_info()
        if self.ws.onerror:
            self.ws.onerror(self.ws, e)
        else:
            asyncore.dispatcher.handle_error(self)

    def handle_close(self):
        self.close()
        if self.ws.onclose:
            self.ws.onclose(self.ws)

    def handle_read(self):
        if self._handshake_complete:
            self._read_until('\xff', self._handle_frame)
        else:
            self._read_until('\r\n\r\n', self._handle_header)

    def handle_write(self):
        sent = self.send(self._write_buffer)
        self._write_buffer = self._write_buffer[sent:]

    def writable(self):
        return len(self._write_buffer) > 0

    def write(self, data):
        self._write_buffer += data # TODO: separate buffer for handshake from data to
                                   # prevent mix-up when send() is called before
                                   # handshake is complete?

    def _read_until(self, delimiter, callback):
        self._read_buffer += self.recv(4096)
        pos = self._read_buffer.find(delimiter)+len(delimiter)+1
        if pos > 0:
            data = self._read_buffer[:pos]
            self._read_buffer = self._read_buffer[pos:]
            if data:
                callback(data)

    def _handle_frame(self, frame):
        if frame[-1] != '\xff':
            raise WebSocketError("Frame didn't end right")
        if frame[0] != '\x00':
            raise WebSocketError("Frame didn't begin right")

        if self.ws.onmessage:
            message = decode_socketio_message(frame[1:-1])
            if isinstance(message, str) and message.startswith(HEARTBEAT_FRAME):
                self.ws.send(message)
            else:
                self.ws.onmessage(self.ws, message)
        # TODO: else raise WebSocketError('No message handler defined')

    def _handle_header(self, header):
        assert header[-4:] == '\r\n\r\n'
        start_line, fields = _parse_http_header(header)
        if start_line != 'HTTP/1.1 101 Web Socket Protocol Handshake' or \
           fields.get('Connection', None) != 'Upgrade' or \
           fields.get('Upgrade', None) != 'WebSocket':
            raise WebSocketError('Invalid server handshake')

        self._handshake_complete = True
        if self.ws.onopen:
            self.ws.onopen(self.ws)

_IPV4_RE = re.compile(r'\.\d+$')
_PATH_SEP = re.compile(r'/+')

def _parse_http_header(header):
    def split_field(field):
        k, v = field.split(':', 1)
        return (k, v.strip())

    lines = header.strip().split('\r\n')
    if len(lines) > 0:
        start_line = lines[0]
    else:
        start_line = None

    return (start_line, dict(map(split_field, lines[1:])))

def _eff_host(host):
    if host.find('.') == -1 and not _IPV4_RE.search(host):
        return host + '.local'
    return host

def _cookie_for_path(cookie, path):
    if not cookie.path or path == '' or path == '/':
        return True
    path = _PATH_SEP.split(path)[1:]
    cookie_path = _PATH_SEP.split(cookie.path)[1:]
    for p1, p2 in map(lambda *ps: ps, path, cookie_path):
        if p1 == None:
            return True
        elif p1 != p2:
            return False

    return True

def _cookie_for_domain(cookie, domain):
    if not cookie.domain:
        return True
    elif cookie.domain[0] == '.':
        return domain.endswith(cookie.domain)
    else:
        return cookie.domain == domain

def _utf8(s):
    return s.encode('utf-8')

def encode_for_socketio(message):
    """ Encode 'message' string or dictionary to be able to be transported via
    a Python WebSocket client to a Socket.IO server (which is capable of
    receiving WebSocket communications). This method taken from
    gevent-socketio.
    """

    if isinstance(message, basestring):
        encoded_msg = message
    elif isinstance(message, (object, dict)):
        return encode_for_socketio(JSON_FRAME + simplejson.dumps(message))
    else:
        raise ValueError("Can't encode message.")

    return MSG_FRAME + str(len(encoded_msg)) + MSG_FRAME + encoded_msg

def decode_socketio_message(message):
    if message[0:3] != MSG_FRAME:
        raise ValueError("Unsupported frame type: " + message)
    _, size, data = message.split(MSG_FRAME, 2)
    size = int(size)
    frame_type = data[0:3]
    if frame_type == JSON_FRAME:
        data = simplejson.loads(data[3:size])
    return data

