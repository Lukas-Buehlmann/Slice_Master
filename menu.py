import random

import pygame
import sys
import math


WIDTH = 512
HEIGHT = 512

# music from https://www.fesliyanstudios.com/royalty-free-music/downloads-c/japanese-music/63
# credit to Fesliyan Studios
MUSIC_LIST = [
    "Music//A_Geishas_Lament.mp3",
    "Music//Fun_in_Kyoto.mp3",
    "Music//Ninja_Ambush.mp3",
    "Music//Peaceful_Koi_Pond.mp3",
    "Music//Tokyo_Lo-Fi.mp3",
    "Music//Zen_Garden.mp3"
]


class Button:
    def __init__(self, x, y, w, h, text, font_path=None, font_size=12):
        self.hitbox = pygame.Rect(x, y, w, h)
        self.pressed = False
        self.text = text
        self.font = pygame.font.Font(font_path, font_size)

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

    def draw(self, surface, border_colour, font_colour, rounded_rad=-1, border_w=1, centred=True):
        words = self.text.split()
        lines = []
        offset = rounded_rad + self.hitbox.w // 30

        # deal with long word still
        total_width = 0
        sentence = ""
        for word in words:
            w, h = self.font.size(word)
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
            w, h = self.font.size(lines[i])

            if centred:
                dest = self.hitbox.centerx - w // 2, self.hitbox.y + offset // 4 + h * i
                surface.blit(text_surface, dest)
            else:  # left aligned
                dest = self.hitbox.x + offset, self.hitbox.y + offset // 2 + h * i
                surface.blit(text_surface, dest)

        pygame.draw.rect(surface, border_colour, self.hitbox, width=border_w, border_radius=rounded_rad)


class Slider:
    def __init__(self, label, init_value, x, y, w, h, font_path=None, font_size=12):
        self.label = label
        self.font = pygame.font.Font(font_path, font_size)
        self.value = init_value
        self.rect = pygame.Rect(x, y, w, h)

        self.text_w, self.text_h = self.font.size(self.label)  # size of label
        self.num_w, self.num_h = self.font.size("100")  # width of value number at max width (at 100)
        self.offset = w // 20

        self.slider_range = (self.text_w + self.offset, w - self.offset - self.num_w)

    def update(self):
        pygame.event.get()
        for event in pygame.event.get():

        mouse_down = pygame.mouse.get_pressed(num_buttons=3)[0]
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if mouse_down and self.rect.bottom <= mouse_y <= self.rect.top:
            print("test")
            raw_x = clamp(mouse_x, self.slider_range[0], self.slider_range[1])
            raw_x -= self.slider_range[0]  # brings values of x from 0 to slider max

            # map between 0 and 100
            self.value = round((100 * raw_x) / (self.slider_range[1] - self.slider_range[0]))

    def draw(self, surface, colour):

        # draw label
        text_surface = self.font.render(self.label, 1, colour)
        dest = (self.rect.x + self.offset, self.rect.centery - self.text_h // 2)
        surface.blit(text_surface, dest)

        # draw slider
        slider_w = self.slider_range[1] - self.slider_range[0]
        hor_bar = pygame.Rect(
            self.slider_range[0],
            self.rect.centery - self.rect.h // 10,
            slider_w,
            self.rect.h // 5
        )
        pygame.draw.rect(surface, colour, hor_bar)

        # draw tick mark
        vert_bar = pygame.Rect(
            round(self.value * slider_w / 100 - slider_w / 30),
            self.rect.top,
            slider_w // 15,
            self.rect.h
        )
        pygame.draw.rect(surface, colour, vert_bar)

        # draw value
        text_surface = self.font.render(str(self.value), 1, colour)
        dest = (self.slider_range[1] + self.offset, self.rect.centery - self.num_h // 2)
        surface.blit(text_surface, dest)


def clamp(n, small, large):
    """
    Clips a number to be within the interval [small, large]

    :param n: Float
    :param small: Float
    :param large: Float
    :return: Float
    """

    return max(small, min(n, large))



def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    samurai_font = pygame.font.Font("Midorima.ttf", 256)

    res_info = pygame.display.Info()
    win_width = res_info.current_w
    win_height = res_info.current_h

    window = pygame.display.set_mode((win_width, win_height))
    screen = pygame.Surface((WIDTH, HEIGHT))

    rand_nums = [i for i in range(6)]
    music_path = MUSIC_LIST[rand_nums.pop(random.randint(0, len(rand_nums) - 1))]
    current_track = pygame.mixer.Sound(music_path)
    current_track.play()

    # image Designed by Freepik
    bg_img = pygame.image.load("Images//Title_bg.jpg")
    bg_img = pygame.transform.scale(bg_img, (win_width, win_height))

    clock = pygame.time.Clock()

    my_button = Button(50, 50, 200, 100, "Test text box!", font_path="Midorima.ttf", font_size=256)
    play_button = Button(win_width//2 - 200, win_height//2, 400, 100, "Play Game", font_path="Midorima.ttf", font_size=72)
    settings_button = Button(win_width//2 - 200, win_height//2 + 120, 400, 100, "Settings", font_path="Midorima.ttf", font_size=72)

    my_slider = Slider("Volume", 50, 100, 100, 300, 30, font_size=24)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # screen.fill((0, 0, 0))
        window.blit(bg_img, (0, 0))

        w, h = samurai_font.size("Fruit Fury")
        text_surface = samurai_font.render("Fruit Fury", True, (0, 0, 0))
        window.blit(text_surface, (win_width//2 - w//2, 0))

        # my_button.update()
        # my_button.draw(screen, (255, 255, 255), (255, 255, 255), 10, 3)
        play_button.update()
        play_button.draw(window, (255, 255, 255), (255, 255, 255), 10, 3)
        settings_button.update()
        settings_button.draw(window, (255, 255, 255), (255, 255, 255), 10, 3)

        my_slider.update()
        my_slider.draw(window, (255, 255, 255))

        pygame.display.flip()
        clock.tick(165)


if __name__ == "__main__":
    main()
