import pygame
from os import environ
from sys import exit

# Define some variables
SCREENWIDTH=800
SCREENHEIGHT=480
WHITE=(255,255,255)

# Open a new window
environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
size = (SCREENWIDTH, SCREENHEIGHT)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Forest Foes")

# Load Images
background = pygame.image.load("resources/images/pixel_forest.png")
backgroundRect = background.get_rect()

# Configure the text
pygame.font.init()
fnt = pygame.font.SysFont("Arial", 14)
fnt_big = pygame.font.SysFont("Arial", 50)
fnt_med = pygame.font.SysFont("Arial", 30)
txtpos = (100, 90)


# This class represents a player. It derives from the "Sprite" class in Pygame.
class Player(pygame.sprite.Sprite):

    def __init__(self, x_pos=125, y_pos = 270):
        # Call the parent class (Sprite) constructor
        super().__init__()

        # Load the player picture
        self.image = pygame.image.load("resources/images/player.png").convert_alpha()
        # Fetch the rectangle object that has the dimensions of the image.
        size = (width, height) = self.image.get_size()
        self.rect = pygame.Rect(x_pos, y_pos, size[0], size[1])
        self.direction = "left"
        self.display = False
        self.arrows = pygame.sprite.Group()

    # Methods
    @property
    def pos(self):
        return [self.rect.x, self.direction]

    @pos.setter
    def pos(self, x, direction):
        self.rect.x = x
        self.direction = direction

    # Update player's position
    def update(self, pos):
        [x, direction] = pos
        self.rect.x = x
        if direction != self.direction:
            self.image = pygame.transform.flip(self.image, 1, 0)
            self.direction = direction

    def moveRight(self):
        self.rect.x += 5
        if self.direction == "left":
            self.image = pygame.transform.flip(self.image, 1, 0)
            self.direction = "right"

    def moveLeft(self):
        self.rect.x -= 5
        if self.direction == "right":
            self.image = pygame.transform.flip(self.image, 1, 0)
            self.direction = "left"

    def set_p1(self, p1):
        if p1:
            self.update([125, "right"])
        else:
            self.set_p2(True)

    def set_p2(self, p2):
        if p2:
            self.update([SCREENWIDTH-125, "left"])
        else:
            self.set_p1(True)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Tree(Player):
    def __init__(self, x_pos, y_pos=0):
        super().__init__()
        self.image = pygame.image.load("resources/images/tree01.png").convert_alpha()
        self.rect = pygame.Rect(x_pos, y_pos, size[0], size[1])


class Arrow(pygame.sprite.Sprite):
    """ This class represents the arrow . """
    def __init__(self, x_pos, direction):
        # Call the parent class (Sprite) constructor
        super(Arrow, self).__init__()
        self.image = pygame.image.load("resources/images/arrow.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x_pos
        self.rect.y = 330
        self.direction = direction
        if direction == "right":
            self.image = pygame.transform.flip(self.image, 1, 0)
        self.arrow_speed = 1

    def update(self):
        if self.direction == "left":
            self.rect.x -= 1
        if self.direction == "right":
            self.rect.x += 1

    def set_loc(self, x, dir):
        self.rect.x = x
        self.direction = dir

    def get_loc(self):
        return [self.rect.x, self.rect.y]

# Main Client Class
class ForestFoes(object):

    def __init__(self):
        self.statusLabel = "Connecting"
        self.playersLabel = "Waiting for player"
        self.winLoseLabel = ''
        self.restartLabel = 'Press Home button or j key to restart'
        self.frame = 0
        self.p1 = Player()
        self.p2 = Player()
        self.p1.set_p1(True)
        self.p2.set_p2(True)
        self.is_p1 = None
        self.game_over = False
        self.has_won = False
        self.player_list = pygame.sprite.Group()
        self.arrow_list = pygame.sprite.Group()
        self.trees = [Tree(200), Tree(600)]

    # Returns string telling which player the client is
    def which_player(self):
        return str("p1") if self.is_p1 else str("p2")
    
    def update_arrows(self, arrows):
        print("update_arrows")
        self.arrow_list.empty()
        for loc in arrows:
            # Set the arrow's position
            arrow = Arrow(loc[0],loc[1])
            # Add the arrow to the list
            self.arrow_list.add(arrow)

    # Handles PyGame events
    def events(self):
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    print("S pressed")
                    self.player_shoot()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player_move("left")
        if keys[pygame.K_RIGHT]:
            self.player_move("right")

    # Draws all game art assets
    def draw(self):
        # Draw background image
        screen.blit(background, [0, 0])

        # Draw connection and player status
        screen.blit(fnt.render(self.statusLabel, 1, WHITE), [10, 25])
        screen.blit(fnt.render(self.playersLabel, 1, WHITE), [10, 40])

        # Draw Sprites
        if self.p1.display:
            self.p1.draw(screen)
        if self.p2.display:
            self.p2.draw(screen)
        self.arrow_list.draw(screen)
        for tree in self.trees:
            tree.draw(screen)

        pygame.display.flip()
