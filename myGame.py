import pygame, random
from player import Player
pygame.init()

# Define some variables
SCREENWIDTH=800
SCREENHEIGHT=480
WHITE = (255,255,255)

# Open a new window
size = (SCREENWIDTH, SCREENHEIGHT)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Forest Foes")

# Load sprites
all_sprites_list = pygame.sprite.Group()
playerSprite = Player()
playerSprite.rect.x = 125
playerSprite.rect.y = 270

# Load Images
background = pygame.image.load("resources/images/pixel_forest.png")
backgroundRect = background.get_rect()
character = pygame.image.load("resources/images/player.png")

# To allow the player to close the window
carryOn = True
clock = pygame.time.Clock()

# -------- Main Program Loop -----------
while carryOn:
    # --- Main event loop
    for event in pygame.event.get():  # User did something
        if event.type == pygame.QUIT:  # If user clicked close
            carryOn = False  # Flag that we are done so we exit this loop

    # Game logic
    all_sprites_list.update()

    # Drawing on screen
    screen.fill(0)                  # clear screen
    screen.blit(background, (backgroundRect)) # draw background
    #screen.blit(character, (125, 270)) # draw player
    all_sprites_list.draw(screen)   # draw sprites

    # Refresh screen
    pygame.display.flip()

    # Limit to 60 frames per second
    clock.tick(60)

# Once we have exited the main program loop we can stop the game engine:
pygame.quit()
