function on_message(message) {
    if (!message) {
        // Heartbeat message; move along
        return;
    }
    if ('connected' in message) {
        initialize_ui(message);
        refresh_ui(message);
    }
    if ('announcement' in message) {
        // Not sure what to do here yet - this is for things like, "another
        // player connected"
    }
    if ('available' in message) {
        if ($.fn.game_config.player_num == -1) {
            $("#main p").text("Connected! Pick which player to be:");
            var i = 0;
            for (i = 0; i < message.available.length; i++) {
                player_num = message.available[i];
                text = message.available[i];
                button_text = '<button onclick="pick_player(' + player_num;
                button_text += ')">' + text + '</button>';
                $(button_text)
                .appendTo('#main')
                .wrap('<p></p>');
            }
        } else {
            send({'player': $.fn.game_config.player_num});
        }
    }
};

function send(message) {
    $.fn.socket_config.socket.send(message);
};

function initialize_ui(message) {
    // This sets up some mappings between things in the game state and UI
    // elements, like deciding the order of kingdom cards, and the like.
    cardname_to_ui_id = new Array();
    cardname_to_ui_id['Estate'] = '#Estate';
    cardname_to_ui_id['Duchy'] = '#Duchy';
    cardname_to_ui_id['Province'] = '#Province';
    cardname_to_ui_id['Colony'] = '#Colony';
    cardname_to_ui_id['Copper'] = '#Copper';
    cardname_to_ui_id['Silver'] = '#Silver';
    cardname_to_ui_id['Gold'] = '#Gold';
    cardname_to_ui_id['Platinum'] = '#Platinum';
    cardname_to_ui_id['Curse'] = '#Curse';
    kingdom_cards = new Array();
    var card_num = 1;
    for (var i = 0; i < message.game_state.cardstacks.length; i++) {
        cardname = message.game_state.cardstacks[i][0];
        if (cardname == "Colony") {
            $("#Colony").parent().show();
        }
        if (cardname == "Platinum") {
            $("#Platinum").parent().show();
        }
        if (!cardname_to_ui_id.hasOwnProperty(cardname)) {
            cardname_to_ui_id[cardname] = '#kcard' + card_num;
            card_num++;
        }
        $(cardname_to_ui_id[cardname]+' .cardname').text(cardname);
    }
    $.fn.game_state.cardname_to_ui_id = cardname_to_ui_id;
};

function refresh_ui(message) {
    ui_mapping = $.fn.game_state.cardname_to_ui_id;
    for (var i = 0; i < message.game_state.cardstacks.length; i++) {
        cardname = message.game_state.cardstacks[i][0];
        left = message.game_state.cardstacks[i][1];
        $(ui_mapping[cardname]+' .left').text('Left: ' + left);
    }
};

function pick_player(num) {
    window.location = '/game/' + $.fn.game_config.game + '/player/' + num
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
    $.fn.game_state = function() {};
    $("#Colony").parent().hide();
    $("#Platinum").parent().hide();
});
