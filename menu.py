import pygame
import sys
import math


WIDTH = 512
HEIGHT = 512


class Button:
    def __init__(self, x, y, w, h, text, font_style=None, font_size=12):
        self.hitbox = pygame.Rect(x, y, w, h)
        self.pressed = False
        self.text = text
        self.font = pygame.font.Font(font_style, font_size)

    def update(self):
        clicking = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicking = True

        mousepos = pygame.mouse.get_pos()
        self.pressed = (
                clicking and
                self.hitbox.x <= mousepos[0] <= self.hitbox.x + self.hitbox.w and
                self.hitbox.y <= mousepos[0] <= self.hitbox.y + self.hitbox.h
        )

    def draw(self, surface, border_colour, font_colour, rounded_rad=-1, border_w=1):
        words = self.text.split()
        lines = []
        offset = rounded_rad + self.hitbox.w // 30
        height = 0

        # deal with long word still
        total_width = 0
        sentence = ""
        for word in words:
            w, height = self.font.size(word)
            total_width += w
            if total_width > self.hitbox.w - 2*offset:
                total_width = w
                lines.append(sentence)
                sentence = word + ' '
            else:
                sentence += word + ' '
        lines.append(sentence)

        for i in range(len(lines)):
            text_surface = self.font.render(lines[i], 1, font_colour)
            dest = self.hitbox.x + offset, self.hitbox.y + offset // 2 + height * i
            surface.blit(text_surface, dest)

        pygame.draw.rect(surface, border_colour, self.hitbox, width=border_w, border_radius=rounded_rad)


def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    clock = pygame.time.Clock()

    my_button = Button(50, 50, 200, 100, "Test text box!", font_size=36)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        screen.fill((0, 0, 0))

        my_button.update()
        my_button.draw(screen, (255, 255, 255), (255, 255, 255), 10, 3)

        pygame.display.flip()
        clock.tick(165)


if __name__ == "__main__":
    main()
