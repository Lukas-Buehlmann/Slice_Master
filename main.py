import numpy as np
import cv2

KERNEL_SIZE = 5

# a class to isolate a given colour and apply effects to it
class Colour:
    def __init__(self, h, sens, name, data_hsv):
        self.mask = None

        # catches hue values that are too low
        h_diff = h - sens
        if h_diff < 0:
            h -= h_diff

        # isolate the colour
        lower = np.array([h - sens, 100, 100], np.uint8)
        upper = np.array([h + sens, 255, 255], np.uint8)
        self.range = cv2.inRange(data_hsv, lower, upper)

    # expands the borders of large patches in colour range. kills noise. based on size
    # https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html - docs for morphological transformation
    def dilate_colour(self, size, frame_data):
        kernel = np.ones((size, size), dtype="uint8")
        self.mask = cv2.dilate(self.range, kernel)

        return cv2.bitwise_and(frame_data, frame_data, mask=self.mask)


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

        # Creating contour to track red color
        contours, hierarchy = cv2.findContours(red.mask,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 300:
                x, y, w, h = cv2.boundingRect(contour)
                frame = cv2.rectangle(frame, (x, y),
                                      (x + w, y + h),
                                      (0, 0, 255), 2)

                cv2.putText(frame, "Red Colour", (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (0, 0, 255))

        # Creating contour to track green color
        contours, hierarchy = cv2.findContours(green.mask,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 300:
                x, y, w, h = cv2.boundingRect(contour)
                frame = cv2.rectangle(frame, (x, y),
                                      (x + w, y + h),
                                      (0, 255, 0), 2)

                cv2.putText(frame, "Green Colour", (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (0, 255, 0))

        # Creating contour to track blue color
        contours, hierarchy = cv2.findContours(blue.mask,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)
        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 300:
                x, y, w, h = cv2.boundingRect(contour)
                frame = cv2.rectangle(frame, (x, y),
                                      (x + w, y + h),
                                      (255, 0, 0), 2)

                cv2.putText(frame, "Blue Colour", (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (255, 0, 0))

        # Program Termination
        cv2.imshow("Multiple Color Detection in Real-Time", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            camera.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    main()
