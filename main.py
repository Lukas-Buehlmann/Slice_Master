import numpy as np
import cv2


class Colour:
    def __init__(self, h, sens, name, data_hsv):

        lower = np.array([h - sens, 100, 100], np.uint8)
        upper = np.array([h + sens, 255, 255], np.uint8)
        self.range = cv2.inRange(hsvData, red_lower, red_upper)


def main():

    # creates an object that holds default device camera values
    camera = cv2.VideoCapture(0)

    while True:

        # grabs the frame data
        frame = camera.read()[1]

        # convert rgb to hsv
        hsv_data = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Set up lower and upper bounds for each desired colour---------------------------------------------------------
        # np.uint8 sets array data type to 8-bit unsigned integers
        red_lower = np.array([0, 100, 100], np.uint8)
        red_upper = np.array([2 * SENSITIVITY, 255, 255], np.uint8)
        red_range = cv2.inRange(hsvData, red_lower, red_upper)

        green_lower = np.array([60 - SENSITIVITY, 100, 100], np.uint8)
        green_upper = np.array([60 + SENSITIVITY, 255, 255], np.uint8)
        green_range = cv2.inRange(hsvData, green_lower, green_upper)

        blue_lower = np.array([120 - SENSITIVITY, 100, 100], np.uint8)
        blue_upper = np.array([120 + SENSITIVITY, 255, 255], np.uint8)
        blue_range = cv2.inRange(hsvData, blue_lower, blue_upper)

        # Use a matrix to isolate desired colours-----------------------------------------------------------------------
        # https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html - docs for morphological transformation

        kernel = np.ones((5, 5), dtype="uint8")  # creates a 5x5 matrix. Size determines dilation strength

        # Expands the borders of the mask: image dilation
        red_mask = cv2.dilate(red_range, kernel)
        # isolate colours in the given range
        red_result = cv2.bitwise_and(frame, frame, mask=red_mask)

        # green
        green_mask = cv2.dilate(green_range, kernel)
        green_result = cv2.bitwise_and(frame, frame, mask=green_mask)

        # blue
        blue_mask = cv2.dilate(blue_range, kernel)
        blue_result = cv2.bitwise_and(frame, frame, mask=blue_mask)

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if (area > 300):
                x, y, w, h = cv2.boundingRect(contour)
                imageFrame = cv2.rectangle(imageFrame, (x, y),
                                           (x + w, y + h),
                                           (0, 0, 255), 2)

                cv2.putText(imageFrame, "Red Colour", (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (0, 0, 255))

            # Creating contour to track green color
        contours, hierarchy = cv2.findContours(green_mask,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if (area > 300):
                x, y, w, h = cv2.boundingRect(contour)
                imageFrame = cv2.rectangle(imageFrame, (x, y),
                                           (x + w, y + h),
                                           (0, 255, 0), 2)

                cv2.putText(imageFrame, "Green Colour", (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (0, 255, 0))

            # Creating contour to track blue color
        contours, hierarchy = cv2.findContours(blue_mask,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)
        for pic, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if (area > 300):
                x, y, w, h = cv2.boundingRect(contour)
                imageFrame = cv2.rectangle(imageFrame, (x, y),
                                           (x + w, y + h),
                                           (255, 0, 0), 2)

                cv2.putText(imageFrame, "Blue Colour", (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (255, 0, 0))

            # Program Termination
        cv2.imshow("Multiple Color Detection in Real-Time", imageFrame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            camera.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    main()
