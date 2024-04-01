import numpy as np
import cv2
import pygame
import sys
import math
import random
from menu import Button, Slider
import time

KERNEL_SIZE = 25

WIDTH = 600
HEIGHT = 500

TARGET_RAD = 15

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

FRUIT_IMAGES = [
    ("Images//Apple.png", (255, 0, 0)),
    ("Images//Coconut.png", (255, 255, 255)),
    ("Images//Lemon.png", (255, 255, 0)),
    ("Images//Lime.png", (60, 255, 30)),
    ("Images//Orange.png", (255, 180, 0)),
    ("Images//Peach.png", (255, 114, 22)),
    ("Images//Pomegranate.webp", (255, 80, 80))
]


# a class to isolate a given colour and apply effects to it
class Colour:
    def __init__(self, h, sens, name, data_hsv, minimum_s=100, minimum_v=100, maximum_s=255, maximum_v=255):
        self.mask = None
        self.name = name
        self.origin_h = h
        self.h = h

        # catches hue values that are too low
        h_diff = self.h - sens
        if h_diff < 0:
            self.h -= h_diff

        # isolate the colour
        lower = np.array([self.h - sens, minimum_s, minimum_v], np.uint8)
        upper = np.array([self.h + sens, maximum_s, maximum_v], np.uint8)
        self.range = cv2.inRange(data_hsv, lower, upper)

    # expands the borders of large patches in colour range. kills noise. based on size
    # https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html - docs for morphological transformation
    def dilate_colour(self, size, frame_data):
        kernel = np.ones((size, size), dtype="uint8")
        self.mask = cv2.dilate(self.range, kernel)

        return cv2.bitwise_and(frame_data, frame_data, mask=self.mask)

    # defines the shape of found objects and draws rectangles representing the bounding box
    def get_contour(self, frame_data):
        contours, hierarchy = cv2.findContours(self.mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        colour = self.hsv_to_bgr((self.origin_h, 255, 255))

        rect_list = [colour]

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 800:
                x, y, w, h = cv2.boundingRect(contour)
                rect_list.append(pygame.Rect(x, y, w, h))

                frame_data = cv2.rectangle(
                    frame_data,
                    (x, y),
                    (x + w, y + h),
                    colour,
                    2
                )

                cv2.putText(
                    frame_data,
                    f"{self.name} Colour",
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    colour
                )

        return frame_data, rect_list

    @staticmethod
    def hsv_to_bgr(hsv):
        try:
            h, s, v = hsv

            # print(f"h={h} s={s} v={v}")

            # formula uses s and v as values from 0-1 so dividing by 255^2 maps them properly
            c = (v * s) / (255**2)  # 1 when v and s are 255
            new_h = h / 30  # maps between 0 and 6
            x = c * (1 - math.fabs(new_h % 2 - 1))

            # print(f"new_h={new_h} c={c} x={x}")

            if 0 <= new_h < 1:
                temp = (0, x, c)
            elif 1 <= new_h < 2:
                temp = (0, c, x)
            elif 2 <= new_h < 3:
                temp = (x, c, 0)
            elif 3 <= new_h < 4:
                temp = (0, c, x)
            elif 4 <= new_h < 5:
                temp = (c, 0, x)
            elif 5 <= new_h < 6:
                temp = (x, 0, c)
            else:
                print("h was out of range. returning (0, 0, 0)")
                return (0, 0, 0)

            m = v - c*255
            # print((temp[0]*255 + m, temp[1]*255 + m, temp[2]*255 + m))
            return (temp[0]*255 + m, temp[1]*255 + m, temp[2]*255 + m)

        except UnboundLocalError:
            print("hsv should be a tuple with 3 values. Returning (0, 0, 0)")
        except:
            print("hsv conversion failed. Returning (0, 0, 0)")
            print(f"data entered: h={h} s={s} v={v}")
            return (0, 0, 0)

    @staticmethod
    def bgr_to_rgb(bgr):
        return bgr[2], bgr[1], bgr[0]


class Target:
    def __init__(self, pos, rad, colour, img):
        self.l_pos = list(pos)
        self.r_pos = list(pos)
        self.rad = rad
        self.colour = colour
        self.gravity = 0.5
        self.cut = False
        self.l_v = 0
        self.r_v = 0
        self.y_v = 0
        self.angle = 0
        self.img = img

    # increments the position by given changes in x and y. -1 for side is left, 0 is both, 1 is right
    def incr_pos(self, side, d_x, d_y):
        if side == -1:
            self.l_pos[0] += d_x
            self.l_pos[1] += d_y
        elif side == 0:
            self.l_pos[0] += d_x
            self.l_pos[1] += d_y
            self.r_pos[0] += d_x
            self.r_pos[1] += d_y
        elif side == 1:
            self.r_pos[0] += d_x
            self.r_pos[1] += d_y

    def activate_cut(self, angle):
        self.angle = angle
        self.cut = True
        self.l_v = -random.random() * 5
        self.r_v = random.random() * 5

    def update(self):
        self.y_v += self.gravity
        self.incr_pos(-1, self.l_v, self.y_v)
        self.incr_pos(1, self.r_v, self.y_v)

    def draw(self, surface):
        if self.cut:
            bounds = pygame.Rect(self.l_pos[0] - self.rad, self.l_pos[1] - self.rad, self.rad, self.rad)
            pygame.draw.arc(surface, self.colour, bounds, self.angle, self.angle + math.pi, self.rad)
            bounds = pygame.Rect(self.r_pos[0] - self.rad, self.r_pos[1] - self.rad, self.rad, self.rad)
            pygame.draw.arc(surface, self.colour, bounds, self.angle + math.pi, self.angle, self.rad)
        else:
            surface.blit(self.img, (self.l_pos[0] - self.rad, self.l_pos[1] - self.rad))
            # pygame.draw.circle(surface, self.colour, self.l_pos, self.rad)


class Particle:
    def __init__(self, pos, strength, size, colour):
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        self.colour = colour
        self.GRAV = 0.5
        angle = random.random() * math.pi * 2
        x = strength * math.cos(angle)
        y = strength * -math.sin(angle)
        self.v = pygame.math.Vector2(x, y)

    def update(self):
        self.v.y += self.GRAV
        self.pos += self.v

    def draw(self, surface):
        rect = pygame.Rect(self.pos.x, self.pos.y, self.size, self.size)
        pygame.draw.rect(surface, self.colour, rect)


class Ball:
    def __init__(self, pos, r, colour):
        self.pos = pos
        self.x, self.y = pos
        self.rad = r
        self.colour = colour

    def update(self):
        self.rad -= 0.5

    def draw(self, surface):
        pygame.draw.circle(surface, self.colour, (self.x, self.y), self.rad)


def create_patterns(width, height, framerate):
    patterns = []

    # all patterns are lists of tuples that follow (x_pos, y_vel)

    # from top left to bottom right
    pat = []
    top_v = (height * 4/5 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append(((width * (i+1)) // 6, top_v - i))
    patterns.append(pat)

    # from bottom left to top right
    pat = []
    top_v = (height * 4/5 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append(((width * (i + 1)) // 6, top_v - 4 + i))
    patterns.append(pat)

    # row at top
    pat = []
    top_v = (height * 4/5 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append(((width * (i + 1)) // 6, top_v))
    patterns.append(pat)

    # row at middle
    pat = []
    top_v = (height // 2 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append(((width * (i + 1)) // 6, top_v))
    patterns.append(pat)

    # column at left
    pat = []
    top_v = (height * 4/5 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append((width // 6, top_v - i))
    patterns.append(pat)

    # column at right
    pat = []
    top_v = (height * 4/5 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append(((width * 5) // 6, top_v - i))
    patterns.append(pat)

    # column at middle
    pat = []
    top_v = (height * 4/5 + 0.25*framerate**2) / framerate
    for i in range(5):
        pat.append((width // 2, top_v - i))
    patterns.append(pat)

    # random
    pat = []
    half_v = (height * 4/5 + 0.25*framerate**2) / (framerate * 2)
    for i in range(5):
        pat.append((random.randint(width // 6, (width * 5) // 6), random.random() * half_v + math.sqrt(2)*half_v))
    patterns.append(pat)

    return patterns


def choose_music(channel):
    rand_track = random.randint(0, len(MUSIC_LIST) - 1)
    track = pygame.mixer.Sound(MUSIC_LIST[rand_track])
    channel.play(track)


def divide_line(x1, y1, x2, y2, n):
    d_x = x2 - x1
    d_y = y2 - y1
    points = []

    if d_x == 0 and d_y == 0:
        return [(x1, y1)]
    elif d_x == 0:
        y = min(y1, y2)
        while y < max(y1, y2):
            points.append([x1, y])
            y += math.fabs(d_y / n)
        points.append((x1, max(y1, y2)))
        return points

    m = d_y / d_x
    b = y1 - m * x1

    x = min(x1, x2)
    while x < max(x1, x2):
        points.append([x, m * x + b])
        x += math.fabs(d_x / n)
    points.append((max(x1, x2), m * max(x1, x2) + b))

    return points


def get_setting(label):
    with open("settings.txt", 'r') as f:
        try:
            for line in f.readlines():
                line_text = line.split()
                line_text[0] = line_text[0].strip(':')
                if line_text[0] == label:
                    return line_text[1]
            else:
                return None
        except:
            print("error reading file")
            return None


def change_setting(label, value):
    data = []
    with open("settings.txt", 'r') as f:
        try:
            data = f.readlines()
        except:
            print("error reading file")

    with open("settings.txt", 'w') as f:
        try:
            for i in range(len(data)):
                line_text = data[i].split()
                line_text[0] = line_text[0].strip(':')
                if line_text[0] == label:
                    data[i] = label + ': ' + str(value) + '\n'
                    break
            f.writelines(data)
        except:
            print("error reading file")


# combines colliding rects in the list
def merge_rects(rect_list):
    copy_list = rect_list.copy()
    collisions = []
    kill_list = []

    # print("total rects: ", len(copy_list))

    # find groups of colliding rects
    for i in range(len(copy_list)):
        temp_collide = copy_list[i].collidelistall(copy_list)
        temp_collide.sort()
        if len(temp_collide) > 1:
            if temp_collide not in collisions:
                collisions.append(temp_collide)

    # create a new rect from the group
    for group in collisions:
        x = min((copy_list[i].x for i in group))
        y = min((copy_list[i].y for i in group))
        merged_rect = pygame.Rect(
            x,
            y,
            max((copy_list[i].x for i in group)) - x,
            max((copy_list[i].y for i in group)) - y
        )
        copy_list.append(merged_rect)

        # collect all indices to delete later
        for i in group:
            kill_list.append(i)

    kill_list = list(dict.fromkeys(kill_list))
    kill_list.sort()
    # print("dead rects: ", len(kill_list))
    # delete merged rectangles from list from right to left to avoid issues with shifting indices
    for i in range(len(kill_list) - 1, -1, -1):
        copy_list.pop(kill_list[i])

    # print("final length: ", len(copy_list))

    return copy_list


def game_over(surface, sound_channel, score, high_score):

    win_width = surface.get_width()
    win_height = surface.get_height()

    mouse_down = False

    # image Designed by Freepik
    bg_img = pygame.image.load("Images//Title_bg.jpg")
    bg_img = pygame.transform.scale(bg_img, (win_width, win_height))

    clock = pygame.time.Clock()

    init_volume = int(get_setting("volume"))

    title_button = Button(
        win_width // 2 - 200,
        win_height // 2 + 240,
        400,
        100,
        "Quit",
        font_path="Midorima.ttf",
        font_size=72
    )
    play_button = Button(
        win_width // 2 - 200,
        win_height // 2 + 120,
        400,
        100,
        "Play Again",
        font_path="Midorima.ttf",
        font_size=72
    )

    score_text = Button(
        win_width // 4 - 200,
        win_height // 4 + 120,
        400,
        100,
        "Score: " + str(score),
        font_size=72
    )
    high_text = Button(
        win_width * 3 // 4 - 200,
        win_height // 4 + 120,
        400,
        100,
        "High Score: " + str(high_score),
        font_size=72
    )

    if score > high_score:
        high_text.text = "New High Score: " + str(score)

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False
            elif event.type == pygame.USEREVENT:
                choose_music(sound_channel)

        surface.blit(bg_img, (0, 0))

        title_button.update(mouse_down)
        title_button.draw(surface, (255, 255, 255), (255, 255, 255), 10, 3)
        play_button.update(mouse_down)
        play_button.draw(surface, (255, 255, 255), (255, 255, 255), 10, 3)

        score_text.draw(surface, (255, 255, 255), (255, 255, 255), border_w=-1)
        high_text.draw(surface, (255, 255, 255), (255, 255, 255), border_w=-1)

        if title_button.pressed:
            return False
        if play_button.pressed:
            return True

        # sets the volume. Value must be from 0.0-1.0 and self.value is from 0-100
        sound_channel.set_volume(init_volume / 100)

        pygame.display.flip()

        clock.tick(165)


def pause_menu(surface, sound_channel):

    win_width = surface.get_width()
    win_height = surface.get_height()

    mouse_down = False

    # image Designed by Freepik
    bg_img = pygame.image.load("Images//Title_bg.jpg")
    bg_img = pygame.transform.scale(bg_img, (win_width, win_height))

    clock = pygame.time.Clock()

    init_volume = int(get_setting("volume"))
    sens = int(get_setting("sens"))
    min_v = int(get_setting("min_v"))
    max_v = int(get_setting("max_v"))
    min_s = int(get_setting("min_s"))
    max_s = int(get_setting("max_s"))

    back_button = Button(
        win_width // 2 - 200,
        win_height // 2 + 240,
        400,
        100,
        "Back",
        font_path="Midorima.ttf",
        font_size=72
    )

    v_slider = Slider("Volume", init_volume, win_width // 2 - 300, win_height // 3, 600, 40, font_size=36)
    sens_slider = Slider("Sensitivity", sens, win_width // 2 - 300, win_height // 3 + 60, 600, 40, font_size=36, max_val=15)
    min_v_slider = Slider("Minimum value", min_v, win_width // 2 - 300, win_height // 3 + 120, 600, 40, font_size=36, max_val=255)
    max_v_slider = Slider("Maximum value", max_v, win_width // 2 - 300, win_height // 3 + 180, 600, 40, font_size=36, max_val=255)
    min_s_slider = Slider("Minimum saturation", min_s, win_width // 2 - 300, win_height // 3 + 240, 600, 40, font_size=36, max_val=255)
    max_s_slider = Slider("Maximum saturation", max_s, win_width // 2 - 300, win_height // 3 + 300, 600, 40, font_size=36, max_val=255)

    camera = cv2.VideoCapture(0)

    while True:
        # CV2 Process---------------------------------------------------------------------------------------------------
        rects = []

        # grabs the frame data
        frame = camera.read()[1]
        frame = cv2.flip(frame, 1)

        # convert rgb to hsv
        hsv_data = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Set up lower and upper bounds for each desired colour

        yellow = Colour(30, sens, "yellow", hsv_data, minimum_v=min_v, maximum_v=max_v, minimum_s=min_s, maximum_s=max_s)  # min_v=130
        yellow.dilate_colour(KERNEL_SIZE, frame)

        frame, temp_rects = yellow.get_contour(frame)
        rects.append(temp_rects)

        frame_rgb = frame.transpose([1, 0, 2])
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        colour_viewer = pygame.surfarray.make_surface(frame_rgb)

        # cv2.imshow("Colour Detection Viewer", frame)
        # End of CV2 Process--------------------------------------------------------------------------------------------

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False
            elif event.type == pygame.USEREVENT:
                choose_music(sound_channel)

        surface.blit(bg_img, (0, 0))

        back_button.update(mouse_down)
        back_button.draw(surface, (255, 255, 255), (255, 255, 255), 10, 3)

        # update and draw all sliders. These should really be in a list
        v_slider.update(mouse_down)
        v_slider.draw(surface, (255, 255, 255))
        sens_slider.update(mouse_down)
        sens_slider.draw(surface, (255, 255, 255))
        min_v_slider.update(mouse_down)
        min_v_slider.draw(surface, (255, 255, 255))
        max_v_slider.update(mouse_down)
        max_v_slider.draw(surface, (255, 255, 255))
        min_s_slider.update(mouse_down)
        min_s_slider.draw(surface, (255, 255, 255))
        max_s_slider.update(mouse_down)
        max_s_slider.draw(surface, (255, 255, 255))

        if back_button.pressed:
            break

        # sets the volume. Value must be from 0.0-1.0 and self.value is from 0-100
        sound_channel.set_volume(v_slider.value / 100)
        if v_slider.value != init_volume:
            change_setting("volume", v_slider.value)
            init_volume = v_slider.value

        # sets the sensitivity. Value should be from 0-15 and self.value is from 0-15
        if sens_slider.value != sens:
            change_setting("sens", sens_slider.value)
            sens = sens_slider.value

        # sets the minimum value to detect. Value must be from 0-255 and self.value is from 0-255
        if min_v_slider.value != min_v:
            change_setting("min_v", min_v_slider.value)
            min_v = min_v_slider.value

        # sets the maximum value to detect. Value must be from 0-255 and self.value is from 0-255
        if max_v_slider.value != max_v:
            change_setting("max_v", max_v_slider.value)
            max_v = max_v_slider.value

        # sets the minimum value to detect. Value must be from 0-255 and self.value is from 0-255
        if min_s_slider.value != min_s:
            change_setting("min_s", min_s_slider.value)
            min_s = min_s_slider.value

        # sets the minimum value to detect. Value must be from 0-255 and self.value is from 0-255
        if max_s_slider.value != max_s:
            change_setting("max_s", max_s_slider.value)
            max_s = max_s_slider.value

        colour_viewer = pygame.transform.scale(colour_viewer, (win_width//2 - 350, (win_width//2 - 350) * colour_viewer.get_height() / colour_viewer.get_width()))
        surface.blit(colour_viewer, (0, 0))

        pygame.display.flip()

        clock.tick(165)


def title_screen(surface, sound_channel):
    samurai_font = pygame.font.Font("Midorima.ttf", 256)

    win_width = surface.get_width()
    win_height = surface.get_height()

    mouse_down = False

    # image Designed by Freepik
    bg_img = pygame.image.load("Images//Title_bg.jpg")
    bg_img = pygame.transform.scale(bg_img, (win_width, win_height))

    clock = pygame.time.Clock()

    init_volume = int(get_setting("volume"))

    play_button = Button(
        win_width // 2 - 200,
        win_height // 2,
        400,
        100,
        "Play Game",
        font_path="Midorima.ttf",
        font_size=72
    )
    settings_button = Button(
        win_width // 2 - 200,
        win_height // 2 + 120,
        400,
        100,
        "Settings",
        font_path="Midorima.ttf",
        font_size=72
    )
    quit_button = Button(
        win_width // 2 - 200,
        win_height // 2 + 240,
        400,
        100,
        "Quit",
        font_path="Midorima.ttf",
        font_size=72
    )

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False
            elif event.type == pygame.USEREVENT:
                choose_music(sound_channel)
                sound_channel.set_volume(init_volume)

        # screen.fill((0, 0, 0))
        surface.blit(bg_img, (0, 0))

        w, h = samurai_font.size("Slice Master")
        text_surface = samurai_font.render("Slice Master", True, (0, 0, 0))
        surface.blit(text_surface, (win_width // 2 - w // 2, 0))

        play_button.update(mouse_down)
        play_button.draw(surface, (255, 255, 255), (255, 255, 255), 10, 3)
        settings_button.update(mouse_down)
        settings_button.draw(surface, (255, 255, 255), (255, 255, 255), 10, 3)
        quit_button.update(mouse_down)
        quit_button.draw(surface, (255, 255, 255), (255, 255, 255), 10, 3)

        if play_button.pressed:
            mouse_down = False
            break

        if settings_button.pressed:
            mouse_down = False
            pause_menu(surface, sound_channel)
            init_volume = int(get_setting("volume"))

        if quit_button.pressed:
            pygame.quit()
            sys.exit()

        sound_channel.set_volume(init_volume / 100)

        pygame.display.flip()
        clock.tick(165)


def main():

    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    font = pygame.font.Font(None, 72)
    score = 0
    high_score = int(get_setting("high_score"))

    res_info = pygame.display.Info()
    win_width = res_info.current_w
    win_height = res_info.current_h

    window = pygame.display.set_mode((win_width, win_height))
    screen = pygame.Surface((WIDTH, HEIGHT))

    pygame.display.set_caption("Slice Master")

    clock = pygame.time.Clock()

    balls = [[]]
    avg_ball = []
    old_pos = []
    for i in balls:
        avg_ball.append(Ball((WIDTH // 2, HEIGHT // 2), 8, (255, 0, 0)))
        old_pos.append((WIDTH // 2, HEIGHT // 2))
    # ball1 = Ball((WIDTH // 2, HEIGHT // 2), 8, (255, 0, 0))

    # only can queue one after initial. FIX THIS
    channel = pygame.mixer.Channel(0)
    choose_music(channel)
    channel.set_endevent(pygame.USEREVENT)

    targets = []
    particles = []

    trail = []

    title_screen(window, channel)

    init_volume = int(get_setting("volume"))
    sens = int(get_setting("sens"))
    min_v = int(get_setting("min_v"))
    max_v = int(get_setting("max_v"))
    min_s = int(get_setting("min_s"))
    max_s = int(get_setting("max_s"))

    # Run loading screen before attempting to load camera
    screen.fill((0, 0, 0))
    load_text = Button(WIDTH // 4, HEIGHT // 2 - 18, WIDTH // 2, 50, "Loading...", font_size=36)
    load_text.draw(screen, (0, 0, 0), (255, 255, 255))
    window.blit(screen, (win_width//2 - WIDTH//2, win_height//2 - HEIGHT//2))
    pygame.display.flip()

    # creates an object that holds default device camera values
    camera = cv2.VideoCapture(0)

    bg_img = pygame.image.load("Images//BG_4.jpg")
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    fruit_img = pygame.image.load("Images//Pomegranate.webp")
    fruit_img = pygame.transform.scale(fruit_img, (30, 30))

    # image Designed by Freepik
    win_bg_img = pygame.image.load("Images//Title_bg.jpg")
    win_bg_img = pygame.transform.scale(win_bg_img, (win_width, win_height))

    start_time = time.time()

    framerate = camera.get(cv2.CAP_PROP_FPS)
    framecount = 0
    next_target_frame = framerate * random.randint(1, 3)

    patterns = create_patterns(WIDTH, HEIGHT, framerate)

    while True:

        # CV2 Process---------------------------------------------------------------------------------------------------
        rects = []

        # grabs the frame data
        frame = camera.read()[1]
        frame = cv2.flip(frame, 1)

        # convert rgb to hsv
        hsv_data = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Set up lower and upper bounds for each desired colour
        yellow = Colour(30, sens, "yellow", hsv_data, minimum_v=min_v, maximum_v=max_v, minimum_s=min_s, maximum_s=max_s)  # min_v=130
        yellow.dilate_colour(KERNEL_SIZE, frame)

        # finds the location of all patches of the given colours. Stores in a list of rectangles
        frame, temp_rects = yellow.get_contour(frame)
        rects.append(temp_rects)

        frame_rgb = frame.transpose([1, 0, 2])
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        colour_viewer = pygame.surfarray.make_surface(frame_rgb)

        # cv2.imshow("Colour Detection Viewer", frame)
        # End of CV2 Process--------------------------------------------------------------------------------------------

        # Start of Pygame Process---------------------------------------------------------------------------------------
        framecount += 1
        clock.tick(framerate)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                camera.release()
                pygame.quit()
                cv2.destroyAllWindows()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    camera.release()
                    pygame.quit()
                    cv2.destroyAllWindows()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    bg_img = pygame.image.load(f"Images//BG_{random.randint(1, 4)}.jpg")
                    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
            elif event.type == pygame.USEREVENT:
                choose_music(channel)
                channel.set_volume(init_volume / 100)

        # screen.fill((0, 0, 0))
        screen.blit(bg_img, (0, 0))

        for i in range(len(rects)):
            colour = rects[i][0]
            merged_rects = merge_rects(rects[i][1:])
            for rect in merged_rects:
                balls[i].append(Ball(rect.center, 8, Colour.bgr_to_rgb(colour)))

        for target in targets:
            target.update()
            target.draw(screen)

        for piece in particles:
            piece.update()
            piece.draw(screen)

        connections = []
        for i in range(len(balls)):
            avg = list(avg_ball[i].pos)
            for ball in balls[i]:
                avg[0] += (ball.x - avg[0]) * math.sqrt(ball.rad) / 16
                avg[1] += (ball.y - avg[1]) * math.sqrt(ball.rad) / 16
                ball.update()
                # ball.draw(screen)
            avg_ball[i] = Ball(avg, 8, (0, 0, 255))
            connections.append(avg)
            avg_ball[i].draw(screen)

        for i in range(len(avg_ball)):
            ball_v = (avg_ball[i].pos[0] - old_pos[i][0]), (avg_ball[i].pos[1] - old_pos[i][1])
            ball_speed = math.sqrt(ball_v[0]**2 + ball_v[1]**2)
            points = divide_line(old_pos[i][0], old_pos[i][1], avg_ball[i].pos[0], avg_ball[i].pos[1], ball_speed)

            for point in points:
                trail.append(Ball(point, 8, (255, 240, 0)))

            old_pos[i] = avg_ball[i].pos

            for target in targets:
                if not target.cut:
                    if math.sqrt((avg_ball[i].pos[0] - target.l_pos[0])**2 + (avg_ball[i].pos[1] - target.l_pos[1])**2) < avg_ball[i].rad + TARGET_RAD:
                        if ball_v[0] == 0:
                            angle = math.pi / 2
                        else:
                            angle = math.atan(-ball_v[1] / ball_v[0])
                        target.activate_cut(angle)
                        score += 1
                        for j in range(300):
                            particles.append(Particle(target.l_pos, random.random() * 5, 3, target.colour))
                        # target = Target((random.randint(0, WIDTH), random.randint(0, HEIGHT)), 20, (255, 0, 0))

        # pygame.draw.line(screen, (255, 255, 255), tuple(connections[0]), tuple(connections[1]), 8)

        for ball in trail:
            ball.update()
            ball.draw(screen)

        for i in range(len(trail) - 1, -1, -1):
            if trail[i].rad <= 0:
                trail.pop(i)

        for ball_type in balls:
            for i in range(len(ball_type) - 1, -1, -1):
                if ball_type[i].rad <= 0:
                    ball_type.pop(i)

        for i in range(len(particles) - 1, -1, -1):
            if particles[i].pos.y > HEIGHT:
                particles.pop(i)

        for i in range(len(targets) - 1, -1, -1):
            if targets[i].l_pos[1] > HEIGHT and targets[i].r_pos[1] > HEIGHT:
                targets.pop(i)

        if framecount >= next_target_frame:
            pattern = patterns[random.randint(0, len(patterns) - 1)]
            src, colour = FRUIT_IMAGES[random.randint(0, len(FRUIT_IMAGES) - 1)]
            img = pygame.image.load(src)
            img = pygame.transform.scale(img, (TARGET_RAD*2, TARGET_RAD*2))
            for line in pattern:
                target = Target((line[0], HEIGHT + 4), TARGET_RAD, colour, img)
                target.y_v = -line[1]
                rand_num = random.random()*2 - 1
                target.l_v = rand_num
                target.r_v = rand_num
                targets.append(target)
            next_target_frame = framecount + framerate * random.randint(1, 2)

        # for i in range(len(targets)):
        #     if targets[i].l_pos[1] > HEIGHT and targets[i].r_pos[1] > HEIGHT:
        #         target = Target((random.randint(30, WIDTH-30), HEIGHT), 20, (255, 0, 0))
        #         target.y_v = -20
        #         rand_num = random.random()*4
        #         target.l_v = rand_num
        #         target.r_v = rand_num
        #         targets[i] = target

        elapsed_time = int(start_time - time.time() + 60)
        if elapsed_time <= 0:
            if score > high_score:
                change_setting("high_score", score)
            play_again = game_over(window, channel, score, high_score)
            if play_again:
                score = 0
                high_score = int(get_setting("high_score"))
                start_time = time.time()
                framecount = 0
                next_target_frame = 3*framerate
                targets = []
            else:
                break

        window.blit(win_bg_img, (0, 0))

        new_w = WIDTH * (win_height / HEIGHT)
        screen_surface = pygame.transform.scale(screen, (new_w, win_height))
        window.blit(screen_surface, (win_width - new_w, 0))

        new_h = (win_width - new_w) * colour_viewer.get_height() / colour_viewer.get_width()
        colour_viewer = pygame.transform.scale(colour_viewer, (win_width - new_w, new_h))
        window.blit(colour_viewer, (0, 0))

        text = font.render("Score: " + str(score), True, (255, 255, 255))
        window.blit(text, ((win_width - new_w) // 10, new_h + win_height // 20))

        text = font.render("Time: " + str(elapsed_time), True, (255, 255, 255))
        window.blit(text, ((win_width - new_w) // 10, new_h + win_height // 20 + 60))

        text = font.render("High Score: " + str(high_score), True, (255, 255, 255))
        window.blit(text, ((win_width - new_w) // 10, new_h + win_height // 20 + 180))

        pygame.display.flip()

        # End of Pygame Process-----------------------------------------------------------------------------------------

    # End of main loop - Begin end process------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
