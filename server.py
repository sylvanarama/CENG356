import sys
import os
import pygame
from collections import deque
import random
from time import sleep
from ForestFoes import Player, Arrow, Tree
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

X_DIM = 720
Y_DIM = 480
NUM_TREES = 3
TREE_WIDTH = 370
MAX_PAGE = 2
SCREENSIZE = (X_DIM, Y_DIM)

# Server representation of a single connected client
class ServerChannel(Channel):

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.id = str(self._server.next_id())
        self._player_pos = None
        self.bg_page = 0
        self.p1 = None
        self.p2 = None
        self.sprite = Player(1)  # Each player needs a sprite representation
        self.arrows = pygame.sprite.Group() # Each player has a list of arrows

    @property
    def player_pos(self):
        return self._player_pos

    @player_pos.setter
    def player_pos(self, value):
        self.sprite.update(value)
        self._player_pos = self.sprite.rect.x, self.sprite.direction

    def which_player(self):
        return str("p1") if self.p1 else str("p2")

    # Pass on data to all connected clients
    def pass_on(self, data):
        self._server.send_to_all(data)

    # PodSixNet-defined callback for closing connection
    def Close(self):
        self._server.delete_player(self)


    ##################################
    ### Network specific callbacks ###
    ##################################

    # Processes the "move" action from client
    def Network_move(self, data):
        self.player_pos = data['p_pos']
        self.bg_page = data['p_pg']
        self.pass_on(data)

   # Processes the "shoot" action from client
    def Network_shoot(self, data):
        player = self.sprite
        # Set the arrow so it is where the player is
        arrow = Arrow(*(player.pos), player.bg_page)
        # Add the arrow to the list
        self.arrows.add(arrow)
        # Change the sprite to the "shooting" position
        player.shooting()

        self.pass_on(data)

    # Processes restart from client
    def Network_restart(self, data):
        self._server.restart()

class ForestServer(Server):
    channelClass = ServerChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.p1 = None
        self.p2 = None
        self.ready = False
        self.waiting_player_list = deque()  # Make a FIFO queue for waiting clients (no limit to waiting clients)
        self.tree_pos_list = []
        # Generate random trees
        for i in range(NUM_TREES):
            x_pos = random.randrange(0, X_DIM, TREE_WIDTH)
            page = random.randrange(0, MAX_PAGE, 1)
            self.tree_pos_list.append([page, x_pos, 0])

        print('Server launched')

    ###########################
    ### PodSixNet callbacks ###
    ###########################

    # PodSixNet-defined callback for when a client connects
    def Connected(self, channel, addr):
        if self.p1 and self.p2:
            channel.Send({"action": "init", "p": "full"})
            self.waiting_player_list.append(channel)
        else:
            self.add_player(channel)

    ########################
    ### Server functions ###
    ########################

    # Generates unique ID for each client
    def next_id(self):
        self.id += 1
        return self.id

    # Add a new player
    def add_player(self, player):
        # Determine if P1 or P2
        if self.p1 is None:
            self.p1 = player
            player.p1 = True
            print("New P1 (" + str(player.addr) + ")")
        elif self.p1 and self.p2 is None:
            self.p2 = player
            player.p1 = False
            print("New P2 (" + str(player.addr) + ")")
        else:
            sys.stderr.write("ERROR: Couldn't determine player from client (P1 = "
                             + str(self.p1) + ",  P2 = "
                             + str(self.p2) + ".\n")
            sys.stderr.flush()
            sys.exit(1)
        # If only P1, tell client they're P1
        if self.p2 is None:
            player.Send({"action": "init", "p": 'p1', "trees": self.tree_pos_list})
        # Else if P2, notify P2 and send position data
        else:
            self.p2.Send({"action": "init", "p": 'p2', "trees": self.tree_pos_list})

            self.send_to_all({"action": "ready"})
            # Only send position data from P1 -> P2
            loc = list(self.p1.player_pos)
            pg = self.p1.bg_page
            self.send_to_all({"action": "move", "p": 'p1', "p_pos": loc, "p_pg": pg})
            self.ready = True

    # Deletes a player from the server
    def delete_player(self, player):
        self.ready = False
        if self.p1 is player:
            self.p1 = None
            self.send_to_all({"action": "player_left"})
            print("Deleted P1 (" + str(player.addr) + ")")
        elif self.p2 is player:
            self.p2 = None
            self.send_to_all({"action": "player_left"})
            print("Deleted P2 (" + str(player.addr) + ")")
        elif player in self.waiting_player_list:
            self.waiting_player_list.remove(player)
        else:
            print("ERROR: Can't delete player")
        # Pull waiting player from queue
        if self.waiting_player_list:
            self.add_player(self.waiting_player_list.popleft())

    # Process a player death, end game
    def game_over(self, player):
        dead = player.which_player()
        print(dead, " has died")
        # Send message to clients that a player was defeated
        self.send_to_all({"action": "end", "p": dead})
        self.ready = False

    # Send list of arrow locations to players
    def gen_arrow_locs(self):
        arrow_locs = list()
        for player in {self.p1, self.p2}:
            for arrow in player.arrows:
                # Remove the arrow if it flies off the screen
                if arrow.rect.x < -15 or arrow.rect.x > (X_DIM + 15):
                    arrow.kill()
                    break
                # If we're here, arrow is still moving and should be sent to clients
                arrow_locs.append((arrow.rect.x, arrow.direction, arrow.bg_page))
        return arrow_locs
    
    def handle_arrows(self):
        # Check if there are arrows (if all arrows are cleared, still should update screen to clear arrows)
        player_had_arrows = True if (self.p1.arrows or self.p2.arrows) else False

        # Update arrow positions
        self.p1.arrows.update()
        self.p2.arrows.update()

        # Do collision detection
        self.handle_arrow_hits(self.p1)
        self.handle_arrow_hits(self.p2)

        # Generate position list
        arrow_list = self.gen_arrow_locs()

        # Send new arrow lists
        if arrow_list or player_had_arrows:
            self.send_to_all({"action": "arrows",
                              "arrows": arrow_list,
                              "p1_health": self.p1.sprite.health,
                              "p2_health": self.p2.sprite.health})

    # Collision detection on arrows
    def handle_arrow_hits(self, player):
        if player.p1:
            other_player = self.p2
        else:
            other_player = self.p1

        # Perform collision detection
        arrows_hit = pygame.sprite.spritecollide(player.sprite, other_player.arrows, False)
        # Check the players were in the same room
        if player.bg_page == other_player.bg_page:
            # For each collision, subtract health
            for arrow in arrows_hit:
                arrow.kill()
                player.sprite.health -= 10
                if(player.sprite.health <=0):
                    self.game_over(player)

    # Send data to all connected clients
    def send_to_all(self, data):
        if self.p1 is not None:
            self.p1.Send(data)
        if self.p2 is not None:
            self.p2.Send(data)

    # Main server loop
    def launch_server(self):
        while True:
            self.Pump()
            if self.ready:
                self.handle_arrows()
            sleep(0.0001)  # 0.01, 0.0001?

# get command line argument of server, port
if len(sys.argv) != 2:
    host = "localhost"
    port = "31425"
    s = ForestServer(localaddr=(host, int(port)))
    s.launch_server()
else:
    host, port = sys.argv[1].split(":")
    s = ForestServer(localaddr=(host, int(port)))
    s.launch_server()
