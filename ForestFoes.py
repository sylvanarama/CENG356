import pygame
from os import environ
from sys import exit

# Define some variables
X_DIM = 720
Y_DIM = 480
SCREENSIZE = (X_DIM, Y_DIM)
WHITE=(255, 255, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)
NUM_TREES = 6

# Open a new window
environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
size = (X_DIM, Y_DIM)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Forest Foes")

# Load images
background = pygame.image.load("resources/images/pixel_forest_long.png")
game_over_bg = pygame.image.load("resources/images/game_over.png")
BG_WIDTH = background.get_width()
MAX_PAGE = (BG_WIDTH//X_DIM)-1

# 3.1 - Load audio
hit = pygame.mixer.Sound("resources/audio/hit.wav")
shoot = pygame.mixer.Sound("resources/audio/shoot.wav")
walk = pygame.mixer.Sound("resources/audio/walk.wav")
hit.set_volume(0.5)
shoot.set_volume(0.5)
walk.set_volume(0.025)
pygame.mixer.music.load('resources/audio/Forest_Foes.wav')
pygame.mixer.music.play(-1, 0.0)
pygame.mixer.music.set_volume(0.5)

# Configure the text
pygame.font.init()
fnt = pygame.font.SysFont("Arial", 14)
fnt_big = pygame.font.SysFont("Courier", 50)
fnt_med = pygame.font.SysFont("Courier", 30)
txtpos = (100, 90)


# This class represents a player. It derives from the "Sprite" class in Pygame.
class Player(pygame.sprite.Sprite):

    def __init__(self, player):
        # Call the parent class (Sprite) constructor
        super().__init__()
        if player == 1:
            self.image = pygame.image.load("resources/images/p1_stand.png").convert_alpha()
            self.image = pygame.transform.flip(self.image, 1, 0)
            size = (width, height) = self.image.get_size()
            self.rect = pygame.Rect(125, 270, size[0], size[1])
            self.direction = "right"
            self.bg_page = 0
            self.player = 1
        else:
            self.image = pygame.image.load("resources/images/p2_stand.png").convert_alpha()
            size = (width, height) = self.image.get_size()
            self.rect = pygame.Rect(X_DIM - (125 + size[0]), 270, size[0], size[1])
            self.direction = "left"
            self.bg_page = MAX_PAGE
            self.player = 2
        self.health = 100
        self.mask = pygame.mask.from_surface(self.image)
        self.arrows = pygame.sprite.Group()
        self.hidden = False

    # Methods
    @property
    def pos(self):
        return [self.rect.x, self.direction]

    @pos.setter
    def pos(self, x, direction):
        self.rect.x = x
        self.direction = direction

    # Update player's position
    def update(self, pos, page=None):
        [x, direction] = pos
        if page is None: page = self.bg_page
        if (x < 0) or (x >= X_DIM):
            if direction == "left":
                if page == 0: x = 0
                else:
                    page -=1
                    x = (x % X_DIM)
            elif direction == "right":
                if page == MAX_PAGE: x = X_DIM
                else:
                    page += 1
                    x = (x % X_DIM)

        self.rect.x = x
        self.bg_page = page
        if direction != self.direction:
            self.image = pygame.transform.flip(self.image, 1, 0)
            self.direction = direction
            self.mask = pygame.mask.from_surface(self.image)

    def move(self,direction):
        if direction == "right": self.rect.x += 10
        else: self.rect.x -= 10
        self.update([self.rect.x, direction], self.bg_page)

    def set_p1ayer(self, p1ayer):
        if p1ayer == 1:
            self.image = pygame.image.load("resources/images/p1_stand.png").convert_alpha()
            self.image = pygame.transform.flip(self.image, 1, 0)
            size = (width, height) = self.image.get_size()
            self.rect = pygame.Rect(125, 270, size[0], size[1])
            self.direction = "right"
            self.player = 1
        else:
            self.image = pygame.image.load("resources/images/p2_stand.png").convert_alpha()
            size = (width, height) = self.image.get_size()
            self.rect = pygame.Rect(X_DIM-(125+size[0]), 270, size[0], size[1])
            self.direction = "left"
            self.player = 2
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def shooting(self):
        if self.player == 1:
            self.image = pygame.image.load("resources/images/p1_shoot.png").convert_alpha()
        else:
            self.image = pygame.image.load("resources/images/p2_shoot.png").convert_alpha()
        if self.direction != "left":
            self.image = pygame.transform.flip(self.image, 1, 0)
        self.mask = pygame.mask.from_surface(self.image)

    def standing(self):
        if self.player == 1:
            self.image = pygame.image.load("resources/images/p1_stand.png").convert_alpha()
        else:
            self.image = pygame.image.load("resources/images/p2_stand.png").convert_alpha()
        if self.direction != "left":
            self.image = pygame.transform.flip(self.image, 1, 0)
        self.mask = pygame.mask.from_surface(self.image)

    def reset(self):
        if self.player == 1:
            self.image = pygame.image.load("resources/images/p1_stand.png").convert_alpha()
            self.image = pygame.transform.flip(self.image, 1, 0)
            self.rect.x = 125
            self.direction = "right"
            self.bg_page = 0
        else:
            self.image = pygame.image.load("resources/images/p2_stand.png").convert_alpha()
            size = (width, height) = self.image.get_size()
            self.rect.x = X_DIM - (125 + size[0])
            self.direction = "left"
            self.bg_page = MAX_PAGE
        self.mask = pygame.mask.from_surface(self.image)
        self.health = 100
        self.hidden = False


class Tree(pygame.sprite.Sprite):
    def __init__(self, pos):
        super(Tree, self).__init__()
        self.image = pygame.image.load("resources/images/tree01.png").convert_alpha()
        [page, x_pos] = pos
        self.rect = pygame.Rect(x_pos, 0, size[0], size[1])
        self.bg_page = page

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Arrow(pygame.sprite.Sprite):
    def __init__(self, x_pos, direction, page):
        # Call the parent class (Sprite) constructor
        super(Arrow, self).__init__()
        self.image = pygame.image.load("resources/images/arrow.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x_pos+20
        self.rect.y = 310
        self.direction = direction
        self.bg_page = page
        if direction == "right":
            self.image = pygame.transform.flip(self.image, 1, 0)
        self.arrow_speed = 10

    def update(self):
        if self.direction == "left":
            self.rect.x -= self.arrow_speed
        if self.direction == "right":
            self.rect.x += self.arrow_speed

    def set_loc(self, x, dir, page):
        self.rect.x = x
        self.direction = dir
        self.bg_page = page

    def get_loc(self):
        return [self.rect.x, self.direction, self.bg_page]

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# Main Client Class
class ForestFoes(object):

    def __init__(self):
        self.statusLabel = "Connecting"
        self.playersLabel = "Waiting for player"
        self.winLoseLabel = ''
        self.titleLabel = ''
        self.p1 = Player(1)
        self.p2 = Player(2)
        self.is_p1 = None
        self.game_state = "title"
        self.ready = False
        self.player_list = pygame.sprite.Group()
        self.arrow_list = pygame.sprite.Group()
        self.tree_list = pygame.sprite.Group()

    # Returns string telling which player the client is
    def which_player(self):
        return str("p1") if self.is_p1 else str("p2")

    # Returns the player object which the client is
    def current_player(self):
        return self.p1 if self.is_p1 else self.p2
    
    def update_arrows(self, arrows):
        self.arrow_list.empty()
        for loc in arrows:
            # Set the arrow's position
            arrow = Arrow(loc[0],loc[1],loc[2])
            # Add the arrow to the list
            self.arrow_list.add(arrow)

    def hit(self):
        hit.play()

    # Handles PyGame events
    def events(self):
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and self.game_state == "play":
                    shoot.play()
                    self.player_shoot()
                if event.key == pygame.K_y and self.game_state == "game over":
                    self.game_state = "waiting"
                    self.titleLabel = ">> Lying in Wait <<"
                    self.player_restart()
                if event.key == pygame.K_n and self.game_state == "game over":
                    exit()
        if self.game_state == "play":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                walk.play()
                self.player_move("left")
            if keys[pygame.K_RIGHT]:
                walk.play()
                self.player_move("right")

    # Draws all game art assets
    def draw(self):
        # Title screen
        if self.game_state == "title" or \
                self.game_state == "ready" or \
                self.game_state == "waiting":
            screen.blit(game_over_bg, [0, 0])
            text = fnt_big.render("~ FOREST FOES ~", 1, WHITE)
            textpos = text.get_rect(center=(X_DIM // 2, Y_DIM // 2))
            screen.blit(text, textpos)
            text_2 = fnt_med.render(self.titleLabel, 1, WHITE)
            textpos = text_2.get_rect(center=(X_DIM // 2, Y_DIM // 2 + 50))
            screen.blit(text_2, textpos)

        # Main game
        if self.game_state == "play":
            # P1 Perspective
            if self.is_p1:
                player = self.p1
                # Background
                screen.blit(background, [0, 0], [player.bg_page*X_DIM, 0, X_DIM, Y_DIM])

                # Sprites
                for sprite in self.player_list:
                    if sprite.bg_page == player.bg_page and not sprite.hidden:
                        sprite.draw(screen)
                for sprite in self.arrow_list:
                    if sprite.bg_page == player.bg_page:
                        sprite.draw(screen)
                for sprite in self.tree_list:
                    if sprite.bg_page == player.bg_page:
                        sprite.draw(screen)

                # Health bar
                hp_width = self.p1.health*2
                screen.fill(RED, (10, 25, 200, 15))
                screen.fill(GREEN, (10, 25, hp_width, 15))
                screen.blit(fnt.render("P1 health", 1, WHITE), [10, 5])

            # P2 Perspective
            else:
                player = self.p2
                # Background
                screen.blit(background, [0, 0], [player.bg_page * X_DIM, 0, X_DIM, Y_DIM])

                # Sprites
                for sprite in self.player_list:
                    if sprite.bg_page == player.bg_page and not sprite.hidden:
                        sprite.draw(screen)
                for sprite in self.arrow_list:
                    if sprite.bg_page == player.bg_page:
                        sprite.draw(screen)
                for sprite in self.tree_list:
                    if sprite.bg_page == player.bg_page:
                        sprite.draw(screen)

                # Health bar
                hp_width = self.p2.health*2
                screen.fill(RED, (X_DIM-10-200, 25, 200, 15))
                screen.fill(GREEN, (X_DIM-10-200, 25, hp_width, 15))
                screen.blit(fnt.render("P2 health", 1, WHITE), [X_DIM-10-200, 5])

        # If game over, notify player
        if self.game_state == "game over":
            screen.blit(game_over_bg, [0, 0])

            # Win/lose message
            text_1 = fnt_big.render(self.winLoseLabel, 1, WHITE)
            textpos = text_1.get_rect(center=(X_DIM//2, Y_DIM//2))
            screen.blit(text_1, textpos)
            text_2 = fnt_med.render(">> Play again? [Y/N] <<", 1, WHITE)
            textpos = text_2.get_rect(center=(X_DIM//2, Y_DIM//2+50))
            screen.blit(text_2, textpos)

        # Draw connection and player status
        screen.blit(fnt.render(self.statusLabel, 1, WHITE), [10, Y_DIM-40])
        screen.blit(fnt.render(self.playersLabel, 1, WHITE), [10, Y_DIM-25])

        pygame.display.flip()

        if self.game_state == "title" or \
                self.game_state == "ready":
            pygame.time.wait(1500)
            if self.game_state == "title":
                self.game_state = "waiting"
                self.titleLabel = ">> Lying in Wait <<"
            elif self.game_state == "ready":
                self.game_state = "play"
