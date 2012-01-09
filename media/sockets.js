function on_message(message) {
    if (!message) {
        // Heartbeat message; move along
        return;
    }
    if ('connected' in message) {
        initialize_ui(message);
        $('#main').text(message.count);
        $('#form').css('display', 'block');
    }
    if ('announcement' in message) {
        $('<em>'+esc(message.announcement)+'</em>')
        .appendTo('#main')
        .wrap('<p></p>');
    }
    if ('available' in message) {
        var i = 0;
        for (i = 0; i < message.available.length; i++) {
            player_num = message.available[i];
            text = message.available[i];
            $('<button onclick="player('+player_num+')">'+text+'</button>')
            .appendTo('#main')
            .wrap('<p></p>');
        }
    }
};

function send(message) {
    $.fn.socket_config.socket.send(message);
};

function initialize_ui(message) {
};

function refresh_ui(message) {
};

function player(num) {
    send({'player': num});
};

function esc(msg) {
    return String(msg).replace(/</g, '&lt;').replace(/>/g, '&gt;');
};

$(document).ready(function() {
    $.fn.socket_config.socket = new io.Socket(null,
            {port: $.fn.socket_config.port, rememberTransport: false});
    $.fn.socket_config.socket.connect();
    $.fn.socket_config.socket.on('connect', function(message) {
        send({'game': $.fn.game_config.game});
    });
    $.fn.socket_config.socket.on('message', function(message) {
        on_message(message);
    });
    $.fn.player_state = function() {};
});
