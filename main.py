import numpy as np
import cv2
import pygame
import sys
import math
import random

KERNEL_SIZE = 5

# a class to isolate a given colour and apply effects to it
class Colour:
    def __init__(self, h, sens, name, data_hsv):
        self.mask = None
        self.name = name
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

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 300:
                x, y, w, h = cv2.boundingRect(contour)
                frame_data = cv2.rectangle(
                    frame_data,
                    (x, y),
                    (x + w, y + h),
                    hsv_to_bgr(self.h, 255, 255),
                    2
                )

                cv2.putText(
                    frame_data,
                    f"{self.name} Colour",
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    hsv_to_bgr(self.h, 255, 255)
                )

        return frame_data

    @staticmethod
    def hsv_to_bgr(hsv):
        try:
            h, s, v = hsv

            c = v * s
            new_h = h / 30
            x = c * (1 - math.abs(new_h % 2 - 1))

            if 0 <= new_h < 1:
                return (0, x, c)
            elif 1 <= new_h < 2:
                return (0, c, x)
            elif 2 <= new_h < 3:
                return (x, c, 0)
            elif 3 <= new_h < 4:
                return (0, c, x)
            elif 4 <= new_h < 5:
                return (c, 0, x)
            elif 5 <= new_h < 6:
                return (x, 0, c)
            else:
                print("h was out of range. returning (0, 0, 0)")
                return (0, 0, 0)
        except:
            print("hsv conversion failed. Returning (0, 0, 0)")
            print(f"data entered: h={h} s={s} v={v}")
            return (0, 0, 0)


def main():

    # creates an object that holds default device camera values
    camera = cv2.VideoCapture(0)

    while True:

        # grabs the frame data
        frame = camera.read()[1]

        # convert rgb to hsv
        hsv_data = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Set up lower and upper bounds for each desired colour---------------------------------------------------------
        red = Colour(0, 20, "red", hsv_data)
        red_result = red.dilate_colour(KERNEL_SIZE, frame)

        green = Colour(60, 10, "green", hsv_data)
        green_result = green.dilate_colour(KERNEL_SIZE, frame)

        blue = Colour(120, 20, "blue", hsv_data)
        blue_result = blue.dilate_colour(KERNEL_SIZE, frame)

        frame = red.get_contour(frame)
        frame = green.get_contour(frame)
        frame = blue.get_contour(frame)

        # Program Termination
        cv2.imshow("Multiple Color Detection in Real-Time", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            camera.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    main()
