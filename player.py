import pygame

WHITE = (255, 255, 255)


class Player(pygame.sprite.Sprite):
    # This class represents a player. It derives from the "Sprite" class in Pygame.

    def __init__(self, pos):
        # Call the parent class (Sprite) constructor
        super().__init__()

        # Load the player picture
        self.image = pygame.image.load("resources/images/player.png").convert_alpha()
        # Fetch the rectangle object that has the dimensions of the image.
        size = self.image.get_size()
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])