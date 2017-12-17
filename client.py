import sys
import pygame
from pygame.locals import *
from time import sleep
from PodSixNet.Connection import connection, ConnectionListener
from ForestFoes import ForestFoes, Player, Arrow, Tree

# Main Client Class
class Client(ConnectionListener, ForestFoes):
    def __init__(self, host, port):
        self.Connect((host, port))
        ForestFoes.__init__(self)

    # Main game loop for client
    def Loop(self):
        self.Pump()
        connection.Pump()
        self.events()
        self.draw()

        if "connecting" in self.statusLabel:
            self.statusLabel = "connecting" + "".join(["." for s in range(int(self.frame / 30) % 4)])

    # Send an action to the server
    def send_action(self, action):
        if self.is_p1 is None:
            return
        player = self.current_player()
        pos = player.pos
        pg = player.bg_page
        # Send to server
        connection.Send({"action": action, "p": self.which_player(), "p_pos": pos, "p_pg": pg})

    #######################
    ### Event callbacks ###
    #######################

    def player_move(self, direction):
        if self.is_p1 is None:
            return
        player = self.current_player()
        player.move(direction)
        player.standing()
        self.send_action('move')

    def player_shoot(self):
        if self.is_p1 is None:
            return
        player = self.current_player()
        player.shooting()
        self.send_action('shoot')

    # Display win/lose condition
    def player_end(self, player):
        self.game_state = "game over"
        if (self.is_p1 and player == 'p2') or (not self.is_p1 and player == 'p1'):
            self.winLoseLabel = 'YOU WON THE DAY'
        else:
            self.winLoseLabel = 'YOU LOST YOUR WAY'

    def player_restart(self):
        self.tree_list.empty()
        self.arrow_list.empty()
        self.ready = False
        self.p1.reset()
        self.p2.reset()
        self.send_action('restart')

    ###############################
    ### Network event callbacks ###
    ###############################

    # Perform client setup
    def Network_init(self, data):
        if data["p"] == 'p1':
            self.is_p1 = True
            self.player_list.add(self.p1)
            print("You are P1.")
            # Send position to server
            self.send_action('move')
        elif data["p"] == 'p2':
            self.is_p1 = False
            self.player_list.add(self.p2)
            print('You are P2. The game will start momentarily.')
            # Send position to server
            self.send_action('move')
        elif data["p"] == 'full':
            print('Server is full. You have been placed in a waiting queue.')
            self.playersLabel = "Waiting for free slot in server"
        else:
            sys.stderr.write("ERROR: Couldn't determine player from server.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    # Network is ready, start game
    def Network_ready(self, data):
        self.titleLabel = ">> Loose your arrows! <<"
        self.playersLabel = "You are " + self.which_player().capitalize()
        self.p1.reset()
        self.p2.reset()
        self.player_list.add(self.p1, self.p2)

        for tree_pos in data['trees']:
            self.tree_list.add(Tree(tree_pos))

        self.game_state = "ready"
        self.ready = True

    # Player left network, delete player from client, reset the game
    def Network_player_left(self, data):
        self.playersLabel = "Other player left server"
        if self.game_state == "play":
            self.game_state = "waiting"
            self.titleLabel = ">> Lying in Wait <<"
        if self.is_p1:
            self.player_list.remove(self.p2)
        else:
            self.player_list.remove(self.p1)
        self.player_restart()

    # Update positions of players
    def Network_move(self, data):
        position = data['p_pos']
        page = data['p_pg']
        player = data['p']
        if player == 'p1' and not self.is_p1:
            self.p1.update(position, page)
            self.p1.standing()
        elif player == 'p2' and self.is_p1:
            self.p2.update(position, page)
            self.p2.standing()
        elif player in ('p1', 'p2'):  # This is client's position coming back from player
            pass  # TODO: Anti-cheat detection here
        else:
            sys.stderr.write("ERROR: Couldn't update player movement information.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    # Other client started shooting, change sprite, add arrow to list
    def Network_shoot(self, data):
        player = data['p']
        if player == 'p1' and not self.is_p1:
            self.p1.shooting()
        elif player == 'p2' and self.is_p1:
            self.p2.shooting()

    # Arrow data retrieved from server
    def Network_arrows(self, data):
        self.update_arrows(data['arrows'])
        if(self.p1.health != data['p1_health']):
            self.hit()
            self.p1.health = data['p1_health']
        if (self.p2.health != data['p2_health']):
            self.hit()
            self.p2.health = data['p2_health']

    def Network_hide(self, data):
        if data['p'] == "p1":
            self.p1.hidden = data['hidden']
        else:
            self.p2.hidden = data['hidden']

    # A player has been defeated, end the game
    def Network_end(self, data):
        self.player_end(data['p'])
        self.ready = False

    ########################################
    ### Built-in network event callbacks ###
    ########################################

    # Generic network data callback
    def Network(self, data):
        # print('network:', data)
        pass

    # Player connected to server
    def Network_connected(self, data):
        self.statusLabel = "connected"

    # Server connection error
    def Network_error(self, data):
        print(data)
        import traceback
        traceback.print_exc()
        self.statusLabel = data['error'][1]
        connection.Close()

    # Player disconnected from server
    def Network_disconnected(self, data):
        self.statusLabel += " - disconnected"


if len(sys.argv) != 2:
    host = "localhost"
    port = "31425"
    c = Client(host, int(port))
    while 1:
        c.Loop()
        sleep(0.001)
else:
    host, port = sys.argv[1].split(":")
    c = Client(host, int(port))
    while 1:
        c.Loop()
        sleep(0.001)

