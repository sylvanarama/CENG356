import sys
import pygame
from collections import deque
import random
from time import sleep
from ForestFoes import Player, Arrow, Tree
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

# Define some variables
X_DIM = 720
Y_DIM = 480
SCREENSIZE = (X_DIM, Y_DIM)
WHITE=(255, 255, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)


background = pygame.image.load("resources/images/pixel_forest_long.png")
BG_WIDTH = background.get_width()
MAX_PAGE = (BG_WIDTH//X_DIM)-1
NUM_TREES = MAX_PAGE*3
TREE_WIDTH = 370//2
tree_pos_list = []

# Generate random trees
for i in range(NUM_TREES):
    x_pos = random.randrange(0, X_DIM, TREE_WIDTH)
    page = random.randrange(0, MAX_PAGE, 1)
    tree_pos_list.append([page, x_pos])

# for checking whether players are behind a tree
# 1. page, 2. left boundary, 3. right boundary
tree_boundaries_list = []
for tree in tree_pos_list:
    tree_boundaries_list.append([tree[0], tree[1]+140, tree[1]+190])

# Server representation of a single connected client
# This lass inherits the Player class for simplicity
class ServerChannel(Channel, Player):

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        Player.__init__(self)
        self.id = str(self._server.next_id())
        self.is_p1 = None
        self.restart = False

    # Returns a string telling which player the server channel is
    def which_player(self):
        return str("p1") if self.is_p1 else str("p2")

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
        self.pos = data['p_pos']

        # Check if player is behind a tree
        p_x = self.rect.x+64 # center of player sprite
        p_hidden = False
        for tree in tree_boundaries_list:
            if self.bg_page == tree[0] and tree[1] <= p_x <= tree[2]:
                p_hidden = True

        if self.hidden != p_hidden:
            self.hidden = p_hidden
            self.pass_on({"action": "hide", "p": self.which_player(), "hidden": p_hidden})

        self.pass_on(data)

   # Processes the "shoot" action from client
    def Network_shoot(self, data):
        # Set the arrow so it is where the player is
        arrow = Arrow(data['p_pos'])
        # Add the arrow to the list
        self.arrows.add(arrow)
        self.pass_on(data)

    # Processes restart from client
    def Network_restart(self, data):
        self.reset()
        self.pos = data['p_pos']
        self.restart = True
        print(self.which_player, " restarting")
        self._server.restart(self.which_player())

# This is the main server class
# Handles:
# 1. Adding and deleting players
# 2. game over and restart conditions
# 3. collision detection and arrow management
class ForestServer(Server):
    channelClass = ServerChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.p1 = None
        self.p2 = None
        self.ready = False
        # Make a FIFO queue for waiting clients (no limit to waiting clients)
        self.waiting_player_list = deque()

        print('Server launched')

    ###########################
    ### PodSixNet callbacks ###
    ###########################

    # PodSixNet-defined callback for when a client connects
    def Connected(self, channel, addr):
        if self.p1 and self.p2:
            channel.Send({"action": "init", "p": "full"})
            self.waiting_player_list.append(channel)
            print("New player in queue")
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
            player.is_p1 = True
            player.set_player(1)
            player.Send({"action": "init", "p": 'p1'})
            print("New P1 (" + str(player.addr) + ")")
        elif self.p1 and self.p2 is None:
            self.p2 = player
            player.is_p1 = False
            player.set_player(2)
            player.Send({"action": "init", "p": 'p2'})
            print("New P2 (" + str(player.addr) + ")")

        else:
            sys.stderr.write("ERROR: Couldn't determine player from client (P1 = "
                             + str(self.p1) + ",  P2 = "
                             + str(self.p2) + ".\n")
            sys.stderr.flush()
            sys.exit(1)
        # If both P1 and P2 connected, start the game
        if self.p1 and self.p2:
            self.p1.restart = False
            self.p2.restart = False
            self.ready = True
            self.send_to_all({"action": "ready", "trees": tree_pos_list})


    # Deletes a player from the server
    def delete_player(self, player):
        self.ready = False

        if self.p1 is player:
            self.p1 = None
            self.send_to_all({"action": "player_left"})
            print("Deleted P1 (" + str(player.addr) + ")")
            if self.p2 is not None: self.p2.reset()

        elif self.p2 is player:
            self.p2 = None
            self.send_to_all({"action": "player_left"})
            print("Deleted P2 (" + str(player.addr) + ")")
            if self.p1 is not None: self.p1.reset()

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
        # Reset players so game can be restarted
        self.p1.reset()
        self.p2.reset()
        self.ready = False
        # Send message to clients that a player was defeated
        self.send_to_all({"action": "end", "p": dead})

    def restart(self, player):
        # Error checking: don't restart if < 2 clients connected
        if self.p1 is None or self.p2 is None:
            return

        # Both players have chosen to play again, restart the game
        if self.p1.restart and self.p2.restart:
            # Reset flags
            self.p1.restart = False
            self.p2.restart = False

            # Generate new tree positions for the next game
            global tree_pos_list
            tree_pos_list = []
            for i in range(NUM_TREES):
                x_pos = random.randrange(0, X_DIM, TREE_WIDTH)
                page = random.randrange(0, MAX_PAGE, 1)
                tree_pos_list.append([page, x_pos])

            # for checking whether players are behind a tree
            # 1. page, 2. left boundary, 3. right boundary
            global tree_boundaries_list
            tree_boundaries_list = []
            for tree in tree_pos_list:
                tree_boundaries_list.append([tree[0], tree[1] + 140, tree[1] + 190])

            # Send message to clients that game is ready to start
            self.ready = True
            self.send_to_all({"action": "ready", "trees": tree_pos_list})

    # Update arrow positions, detect collisions, and send data to players
    def handle_arrows(self):
        # Check if there are arrows (if all arrows are cleared, still should update screen to clear arrows)
        player_had_arrows = True if (self.p1.arrows or self.p2.arrows) else False

        # Update arrow positions
        self.p1.arrows.update()
        self.p2.arrows.update()

        # Collision detection on arrows
        for player in {self.p1, self.p2}:
            if player.is_p1:
                other_player = self.p2
            else:
                other_player = self.p1

            # Check the players were in the same room and visible
            if player.bg_page == other_player.bg_page and not player.hidden:
                # For each collision, subtract health
                for arrow in other_player.arrows:
                    if pygame.sprite.collide_mask(arrow, player):
                        arrow.kill()
                        player.health -= 10
                        self.send_to_all({"action": "hit", "p": player.which_player()})
                    # Player was defeated: exit function, end game
                    if (player.health <= 0):
                        self.game_over(player)
                        return

        # Update list of arrow positions
        arrow_list = []
        for player in {self.p1, self.p2}:
            for arrow in player.arrows:
                # Remove the arrow if it flies off the screen
                if arrow.rect.x < -15 or arrow.rect.x > (X_DIM + 15):
                    arrow.kill()
                    break
                # Arrow is still moving and should be sent to clients
                arrow_list.append((arrow.pos))

        # Send new arrow lists to players
        if arrow_list or player_had_arrows:
            self.send_to_all({"action": "arrows", "arrows": arrow_list})

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
            sleep(0.01)  # 0.01, 0.0001?

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
