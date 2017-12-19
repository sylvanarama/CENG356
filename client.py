import sys
import pygame
from pygame.locals import *
from time import sleep
from PodSixNet.Connection import connection, ConnectionListener
from ForestFoes import ForestFoes, Player, Arrow, Tree

# Load audio
hit = pygame.mixer.Sound("resources/audio/hit.wav")
shoot = pygame.mixer.Sound("resources/audio/shoot.wav")
walk = pygame.mixer.Sound("resources/audio/walk.wav")
hit.set_volume(0.5)
shoot.set_volume(0.5)
walk.set_volume(0.025)
pygame.mixer.music.load('resources/audio/Forest_Foes.wav')
pygame.mixer.music.play(-1, 0.0)
pygame.mixer.music.set_volume(0.5)

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
        # Send to server
        connection.Send({"action": action, "p": self.which_player(), "p_pos": pos})

    #######################
    ### Event callbacks ###
    #######################

    def player_move(self, direction):
        if self.is_p1 is None:
            return
        walk.play()
        player = self.current_player()
        player.move(direction)
        player.standing()
        self.send_action('move')

    def player_shoot(self):
        if self.is_p1 is None:
            return
        shoot.play()
        player = self.current_player()
        player.shooting()
        self.send_action('shoot')

    def player_restart(self):
        self.tree_list.empty()
        self.arrow_list.empty()
        self.ready = False
        self.p1.reset()
        self.p2.reset()
        self.send_action('restart')

    def player_leave(self):
        # Call server: delete_player
        quit()

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
        self.tree_list.empty()
        self.arrow_list.empty()
        self.ready = False
        self.p1.reset()
        self.p2.reset()

    # Update positions of players
    def Network_move(self, data):
        position = data['p_pos']
        player = data['p']
        if player == 'p1' and not self.is_p1:
            self.p1.update(position)
            self.p1.standing()
        elif player == 'p2' and self.is_p1:
            self.p2.update(position)
            self.p2.standing()
        elif player in ('p1', 'p2'):  # This is client's position coming back from player
            pass  # TODO: Anti-cheat detection here
        else:
            sys.stderr.write("ERROR: Couldn't update player movement information.\n")
            sys.stderr.write(str(data) + "\n")
            sys.stderr.flush()
            sys.exit(1)

    def Network_hide(self, data):
        if data['p'] == "p1":
            self.p1.hidden = data['hidden']
        else:
            self.p2.hidden = data['hidden']

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

    def Network_hit(self, data):
        player = data['p']
        if player == 'p1':
            self.p1.health -= 10
        elif player == 'p2':
            self.p2.health -= 10
        shoot.play()

    # A player has been defeated, end the game
    def Network_end(self, data):
        player = data['p']
        if (self.is_p1 and player == 'p2') or (not self.is_p1 and player == 'p1'):
            self.winLoseLabel = 'YOU WON THE DAY'
        else:
            self.winLoseLabel = 'YOU LOST YOUR WAY'
        self.ready = False
        self.game_state = "game over"

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

