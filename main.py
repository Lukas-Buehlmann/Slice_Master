import numpy as np
import cv2
import pygame
import sys
import math
import random

KERNEL_SIZE = 20

WIDTH = 512
HEIGHT = 512


# a class to isolate a given colour and apply effects to it
class Colour:
    def __init__(self, h, sens, name, data_hsv):
        self.mask = None
        self.name = name
        self.origin_h = h
        self.h = h

        # catches hue values that are too low
        h_diff = self.h - sens
        if h_diff < 0:
            self.h -= h_diff

        # isolate the colour
        lower = np.array([self.h - sens, 100, 100], np.uint8)
        upper = np.array([self.h + sens, 255, 255], np.uint8)
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


class Ball:
    def __init__(self, pos, r, colour):
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


def main():

    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    clock = pygame.time.Clock()

    balls = []

    # creates an object that holds default device camera values
    camera = cv2.VideoCapture(0)

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
        red = Colour(0, 10, "red", hsv_data)
        red_result = red.dilate_colour(KERNEL_SIZE, frame)

        green = Colour(60, 20, "green", hsv_data)
        green_result = green.dilate_colour(KERNEL_SIZE, frame)

        blue = Colour(120, 20, "blue", hsv_data)
        blue_result = blue.dilate_colour(KERNEL_SIZE, frame)

        # finds the location of all patches of the given colours. Stores in a list of rectangles
        # frame, temp_rects = red.get_contour(frame)
        # rects.append(temp_rects)
        frame, temp_rects = green.get_contour(frame)
        rects.append(temp_rects)
        frame, temp = blue.get_contour(frame)
        rects.append(temp_rects)

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

        screen.fill((0, 0, 0))

        for colour_group in rects:
            colour = colour_group[0]
            merged_rects = merge_rects(colour_group[1:])
            for i in range(len(merged_rects)):
                balls.append(Ball(merged_rects[i].center, 8, Colour.bgr_to_rgb(colour)))

        for ball in balls:
            ball.update()
            ball.draw(screen)

        pygame.display.flip()

        # End of Pygame Process-----------------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
