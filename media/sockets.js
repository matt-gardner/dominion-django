function message(obj){
    if (!obj) {
        // Not sure why this happens sometimes, but it does.
        return;
    }
    if ('count' in obj) {
        $('#main').text(obj.count);
        $('#form').css('display', 'block');
    }
    if ('announcement' in obj) {
        $('<em>'+esc(obj.announcement)+'</em>')
        .appendTo('#main')
        .wrap('<p></p>');
    }
    if ('available' in obj) {
        var i = 0;
        for (i = 0; i < obj.available.length; i++) {
            player_num = obj.available[i];
            text = obj.available[i];
            $('<button onclick="player('+player_num+')">'+text+'</button>')
            .appendTo('#main')
            .wrap('<p></p>');
        }
    }
};

function send(){
    var val = 1;
    $.fn.socket_config.socket.send({'val': val});
};

function player(num){
    $.fn.socket_config.socket.send({'player': num});
};

function esc(msg){
    return String(msg).replace(/</g, '&lt;').replace(/>/g, '&gt;');
};

$(document).ready(function() {
    $.fn.socket_config.socket = new io.Socket(null,
            {port: $.fn.socket_config.port, rememberTransport: false});
    $.fn.socket_config.socket.connect();
    $.fn.socket_config.socket.on('connect', function(obj) {
      $.fn.socket_config.socket.send({'game': $.fn.game_config.game});
    });
    $.fn.socket_config.socket.on('message', function(obj){
        message(obj);
    });
});
