function on_message(message) {
    if (!message) {
        // Heartbeat message; move along
        return;
    }
    else if ('attack_response' in message) {
        if (message.attacking_player == $.fn.game_config.player_num) {
            send(message);
        }
    }
    else if ('connected' in message) {
        initialize_ui(message);
        refresh_ui(message);
    }
    else if ('announcement' in message) {
        // Not sure what to do here yet - this is for things like, "another
        // player connected"
    }
    else if ('available' in message) {
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
    else if ('card_bought' in message) {
        refresh_ui(message);
    }
    else if ('newturn' in message) {
        refresh_ui(message);
    }
    else if ('action_finished' in message) {
        refresh_ui(message);
    }
    else if ('user_action' in message) {
        respond_to_action(message);
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
    base_img = '/media/images/';
    img_end = '-short.jpg';
    for (var i = 0; i < message.game_state.cardstacks.length; i++) {
        var cardname = message.game_state.cardstacks[i][0];
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
        new_src = base_img + cardname + img_end;
        $(cardname_to_ui_id[cardname]+' img').attr("src", new_src);
    }
    $.fn.game_state.cardname_to_ui_id = cardname_to_ui_id;

    // Now the players, so we can update their info when we get it.
    player_num_to_ui_id = new Array();
    var player_num = 1;
    for (i = 1; i < message.game_state.num_players+1; i++) {
        if (i == $.fn.game_config.player_num) continue;
        player_num_to_ui_id[i] = '#other_player' + player_num;
        var $other_player = $(player_num_to_ui_id[i]);
        $other_player.css('opacity', 1);
        // Somewhat of an odd thing that I have to use brackets instead of
        // a dot, even though it's all defined the same in python...
        var player = message.game_state.players[i]
        $other_player.find('.name').text(player.name);
        if (player.human) {
            $other_player.find('.human').text('Human')
        }
        else {
            $other_player.find('.human').text('Computer')
        }
        if (player.connected) {
            $other_player.find('.connected').text('Connected')
        }
        else {
            $other_player.find('.connected').text('Not connected')
        }
        player_num++;
    }
    $.fn.game_state.player_num_to_ui_id = player_num_to_ui_id;
};

function refresh_ui(message) {
    // Refresh card stacks
    ui_mapping = $.fn.game_state.cardname_to_ui_id;
    for (var i = 0; i < message.game_state.cardstacks.length; i++) {
        var cardname = message.game_state.cardstacks[i][0];
        left = message.game_state.cardstacks[i][1];
        $(ui_mapping[cardname]+' .left').text(left);
    }
    // Refresh other player views
    ui_mapping = $.fn.game_state.player_num_to_ui_id;
    for (var i = 1; i < message.game_state.num_players+1; i++) {
        if (i == $.fn.game_config.player_num) continue;
        player = message.game_state.players[i];
        $player = $(ui_mapping[i]);
        $player.find('.hand').find('.count').text(player.cards_in_hand)
        $player.find('.deck').find('.count').text(player.cards_in_deck)
        $player.find('.discard').find('.count').text(player.cards_in_discard)
    }
    $('#player_name').text(message.game_state.current_player_name);
    $('#num_actions').text(message.game_state.current_player_actions);
    $('#num_actions').text(message.game_state.current_player_actions);
    $('#num_coins').text(message.game_state.current_player_coins);
    $('#num_buys').text(message.game_state.current_player_buys);
    // Refresh your own views
    me = message.game_state.players[$.fn.game_config.player_num];
    $('#deck .count').text(me.cards_in_deck)
    $('#discard .count').text(me.cards_in_discard)
    if (message.player_state) {
        $('#handsortable').empty();
        for (i = 0; i < message.player_state.hand.length; i++) {
            $(create_card(message.player_state.hand[i]))
                .appendTo('#handsortable');
        }
        $('#handsortable').sortable({
            stop: function(event, ui) {
                if ($.fn.game_state.dropped) {
                    $.fn.game_state.dropped = false;
                    return false;
                }
            },
            revert: true
        });
    }
    // For some reason I'm getting the droppable.drop method called twice, and
    // it's breaking things...
    $.fn.game_state.bought = false;
};

function create_card(card) {
    // The <li> is so that it works with sortable.  I wish I didn't have to use
    // it, though, so I could stay consistent with divs...  Oh well.
    html = '<li class="cardwrapper"><div class="card" id="'+card[1]+'">';
    html += '<img src="/media/images/' + card[0] + '-short.jpg" ';
    html += 'width="108" height="90">';
    html += '<span class="cardname">' + card[0] + '</span></div></li>';
    return html;
}

function pick_player(num) {
    window.location = '/game/' + $.fn.game_config.game + '/player/' + num
};

function esc(msg) {
    return String(msg).replace(/</g, '&lt;').replace(/>/g, '&gt;');
};

function respond_to_action(message) {
    if (message.user_action == 'discard_to_three') {
        text_to_show = 'Militia! Discard to three cards.';
        text_to_show += '  Drag the cards into this dialog.';
    }
    $dialog = $('<div><div class="text"></div><div class="dialog_cards">'
            +'</div></div>');
    $dialog.find('.dialog_cards').droppable({
        drop: function(event, ui) {
            ui.draggable.appendTo($(this));
            ui.draggable.draggable("option", "revert", false);
            ui.draggable.removeClass('ui-sortable-helper');
            $('#handsortable .ui-sortable-placeholder').remove();
            $('#handsortable').sortable("option", "revert", false);
            $.fn.game_state.dropped = true;
        },
        hoverClass: 'drop_hover'
    });
    response = {
        'responding_player': $.fn.game_config.player_num,
        'attacking_player': message.attacking_player,
        'attack_response': 'pues!'
    };
    $dialog.find('.text').html(text_to_show);
    $dialog.dialog({
        close: function(event, ui) {
            to_discard = [];
            $(this).find('.card').each(function() {
                to_discard.push($(this).attr("id"));
            });
            response['discarded'] = to_discard;
            send(response);
        }
    });
}

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
    $('#other_player1').css('opacity', .25);
    $('#other_player2').css('opacity', .25);
    $('#other_player3').css('opacity', .25);
    $('.cards_in_play').sortable({revert: true});
    $('#cardstacks .cardwrapper').draggable({
        connectToSortable: '.cards_in_play',
        revert: "invalid",
        helper: "clone"});
    $.fn.game_state.dropped = false;
    $.fn.game_state.draggable_sibling = "";
    $('#cards_bought').droppable({
        drop: function(event, ui) {
            ui.draggable.appendTo($(this));
            ui.draggable.draggable("option", "revert", false);
            ui.draggable.removeClass('ui-sortable-helper');
            $('#handsortable .ui-sortable-placeholder').remove();
            $('#handsortable').sortable("option", "revert", false);
            $.fn.game_state.dropped = true;
            if (!$.fn.game_state.bought) {
                send({'buycard': ui.draggable.find('.cardname').text()});
            }
            $.fn.game_state.bought = true;
        },
        hoverClass: 'drop_hover'}
    );
    $('#actions_played').droppable({
        drop: function(event, ui) {
            ui.draggable.appendTo($(this));
            ui.draggable.draggable("option", "revert", false);
            ui.draggable.removeClass('ui-sortable-helper');
            $('#handsortable .ui-sortable-placeholder').remove();
            $('#handsortable').sortable("option", "revert", false);
            $.fn.game_state.dropped = true;
            send({'playaction': ui.draggable.find('.card').attr("id")});
        },
        hoverClass: 'drop_hover'}
    );
    $('#endturn').click(function(){
        send({'endturn': 'endturn'});
        // TODO: put this in a better spot; we need to put "cards in play" into
        // the messages the server sends first
        $('.cards_in_play').empty();
    });
});
