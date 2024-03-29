import numpy as np
import cv2
import pygame
import sys
import math
import random
from menu import Button, Slider
import time

KERNEL_SIZE = 15

WIDTH = 600
HEIGHT = 500

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
    def __init__(self, pos, rad, colour):
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

    def draw(self, surface, src):
        if self.cut:
            bounds = pygame.Rect(self.l_pos[0] - self.rad, self.l_pos[1] - self.rad, self.rad, self.rad)
            pygame.draw.arc(surface, self.colour, bounds, self.angle, self.angle + math.pi, self.rad)
            bounds = pygame.Rect(self.r_pos[0] - self.rad, self.r_pos[1] - self.rad, self.rad, self.rad)
            pygame.draw.arc(surface, self.colour, bounds, self.angle + math.pi, self.angle, self.rad)
        else:
            surface.blit(src, (self.l_pos[0] - self.rad, self.l_pos[1] - self.rad))
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
        self.rad -= 0.1

    def draw(self, surface):
        pygame.draw.circle(surface, self.colour, (self.x, self.y), self.rad)


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


def title_screen(surface):
    samurai_font = pygame.font.Font("Midorima.ttf", 256)

    win_width = surface.get_width()
    win_height = surface.get_height()

    mouse_down = False

    rand_nums = [i for i in range(6)]
    music_path = MUSIC_LIST[rand_nums.pop(random.randint(0, len(rand_nums) - 1))]
    current_track = pygame.mixer.Sound(music_path)
    track_length = current_track.get_length()
    start_time = time.time()
    current_track.play()

    # image Designed by Freepik
    bg_img = pygame.image.load("Images//Title_bg.jpg")
    bg_img = pygame.transform.scale(bg_img, (win_width, win_height))

    clock = pygame.time.Clock()

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

    my_slider = Slider("Volume", 50, 100, 100, 600, 40, font_size=36)

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

        # begin next song when each finishes
        if time.time() - start_time >= track_length:
            music_path = MUSIC_LIST[rand_nums.pop(random.randint(0, len(rand_nums) - 1))]
            current_track = pygame.mixer.Sound(music_path)
            track_length = current_track.get_length()
            start_time = time.time()
            current_track.play()

            # refill song list when all are exhausted
            if len(rand_nums) == 0:
                rand_nums = [i for i in range(6)]

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

        my_slider.update(mouse_down)
        my_slider.draw(surface, (255, 255, 255))

        if play_button.pressed:
            break

        if quit_button.pressed:
            pygame.quit()
            sys.exit()

        # sets the volume. Value must be from 0.0-1.0 and self.value is from 0-100
        current_track.set_volume(my_slider.value / 100)

        pygame.display.flip()
        clock.tick(165)


def main():

    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    font = pygame.font.Font(None, 48)
    score = 0

    res_info = pygame.display.Info()
    win_width = res_info.current_w
    win_height = res_info.current_h

    window = pygame.display.set_mode((win_width, win_height))
    screen = pygame.Surface((WIDTH, HEIGHT))

    clock = pygame.time.Clock()

    balls = [[]]
    avg_ball = []
    old_pos = []
    for i in balls:
        avg_ball.append(Ball((WIDTH // 2, HEIGHT // 2), 8, (255, 0, 0)))
        old_pos.append((WIDTH // 2, HEIGHT // 2))
    # ball1 = Ball((WIDTH // 2, HEIGHT // 2), 8, (255, 0, 0))

    targets = []
    for i in range(10):
        target_1 = Target((random.randint(0, WIDTH), random.randint(0, HEIGHT)), 20, (255, 0, 0))
        targets.append(target_1)
    particles = []

    title_screen(window)

    # Run loading screen before attempting to load camera
    screen.fill((0, 0, 0))
    load_text = Button(WIDTH // 4, HEIGHT // 2 - 18, WIDTH // 2, 50, "Loading...", font_size=36)
    load_text.draw(screen, (0, 0, 0), (255, 255, 255))
    window.blit(screen, (win_width//2 - WIDTH//2, win_height//2 - HEIGHT//2))
    pygame.display.flip()

    # creates an object that holds default device camera values
    camera = cv2.VideoCapture(0)

    bg_img = pygame.image.load(f"Images//BG_{random.randint(1, 4)}.jpg")
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    fruit_img = pygame.image.load("Images//Pomegranate.webp")
    fruit_img = pygame.transform.scale(fruit_img, (30, 30))

    framerate = camera.get(cv2.CAP_PROP_FPS)

    while True:

        # CV2 Process---------------------------------------------------------------------------------------------------
        rects = []

        # grabs the frame data
        frame = camera.read()[1]
        frame = cv2.flip(frame, 1)

        # convert rgb to hsv
        hsv_data = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Set up lower and upper bounds for each desired colour
        red = Colour(0, 10, "red", hsv_data, minimum_s=160, maximum_v=220)
        red_result = red.dilate_colour(KERNEL_SIZE, frame)

        # minimum_v=100, minimum_s=120
        green = Colour(175, 0, "pink", hsv_data, minimum_v=100, minimum_s=120)  # min_v=30
        green_result = green.dilate_colour(KERNEL_SIZE, frame)

        yellow = Colour(30, 10, "yellow", hsv_data, minimum_v=70)  # min_v=130
        yellow_result = yellow.dilate_colour(KERNEL_SIZE, frame)

        blue = Colour(120, 20, "blue", hsv_data)
        blue_result = blue.dilate_colour(KERNEL_SIZE, frame)

        # finds the location of all patches of the given colours. Stores in a list of rectangles
        # frame, temp_rects = red.get_contour(frame)
        # rects.append(temp_rects)
        # frame, temp_rects = green.get_contour(frame)
        # rects.append(temp_rects)
        frame, temp_rects = yellow.get_contour(frame)
        rects.append(temp_rects)
        # frame, temp_rects = blue.get_contour(frame)
        # rects.append(temp_rects)

        cv2.imshow("Colour Detection Viewer", frame)
        # End of CV2 Process--------------------------------------------------------------------------------------------

        # Start of Pygame Process---------------------------------------------------------------------------------------
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

        # screen.fill((0, 0, 0))
        screen.blit(bg_img, (0, 0))

        for i in range(len(rects)):
            colour = rects[i][0]
            merged_rects = merge_rects(rects[i][1:])
            for rect in merged_rects:
                balls[i].append(Ball(rect.center, 8, Colour.bgr_to_rgb(colour)))

        for target in targets:
            target.update()
            target.draw(screen, fruit_img)

        for piece in particles:
            piece.update()
            piece.draw(screen)

        connections = []
        for i in range(len(balls)):
            avg = list(avg_ball[i].pos)
            for ball in balls[i]:
                avg[0] += (ball.x - avg[0]) * ball.rad / 16
                avg[1] += (ball.y - avg[1]) * ball.rad / 16
                ball.update()
                # ball.draw(screen)
            avg_ball[i] = Ball(avg, 8, (0, 0, 255))
            connections.append(avg)
            avg_ball[i].draw(screen)

        for i in range(len(avg_ball)):
            ball_v = (avg_ball[i].pos[0] - old_pos[i][0]), (avg_ball[i].pos[1] - old_pos[i][1])

            for target in targets:
                if not target.cut:
                    if math.sqrt((avg_ball[i].pos[0] - target.l_pos[0])**2 + (avg_ball[i].pos[1] - target.l_pos[1])**2) < avg_ball[i].rad + target_1.rad:
                        if ball_v[0] == 0:
                            angle = math.pi / 2
                        else:
                            angle = math.atan(-ball_v[1] / ball_v[0])
                        target.activate_cut(angle)
                        score += 1
                        for j in range(300):
                            particles.append(Particle(target.l_pos, random.random() * 5, 3, (255, 0, 0)))
                        # target = Target((random.randint(0, WIDTH), random.randint(0, HEIGHT)), 20, (255, 0, 0))

        # pygame.draw.line(screen, (255, 255, 255), tuple(connections[0]), tuple(connections[1]), 8)

        for ball_type in balls:
            for i in range(len(ball_type) - 1, -1, -1):
                if ball_type[i].rad <= 0:
                    ball_type.pop(i)

        for i in range(len(particles) - 1, -1, -1):
            if particles[i].pos.y > HEIGHT:
                particles.pop(i)

        for i in range(len(targets)):
            if targets[i].l_pos[1] > HEIGHT and targets[i].r_pos[1] > HEIGHT:
                target = Target((random.randint(30, WIDTH-30), HEIGHT), 20, (255, 0, 0))
                target.y_v = -20
                rand_num = random.random()*4
                target.l_v = rand_num
                target.r_v = rand_num
                targets[i] = target

        text = font.render(str(score), True, (255, 255, 255))
        screen.blit(text, (WIDTH//2-10, HEIGHT//20))

        new_w = WIDTH * (win_height / HEIGHT)
        screen_surface = pygame.transform.scale(screen, (new_w, win_height))
        window.blit(screen_surface, (win_width//2 - new_w//2, 0))

        pygame.display.flip()

        # End of Pygame Process-----------------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
