
from time import sleep
print("Importing cv2")
import cv2
print("Importing numpy")
import numpy
import math
print("importing i2clcd")
from i2clcd import i2clcd
print("importing picamera2")
from picamera2 import Picamera2

# initialization
print("Initializing")
res = (1920, 1440)

previous_position = None
trail = numpy.zeros((res[1], res[0], 3), numpy.uint8)

h_min = 0
h_max = 20
s_min = 150
s_max = 255
v_min = 200
v_max = 256

hsv_min = (h_min, s_min, v_min)
hsv_max = (h_max, s_max, v_max)

# init lcd
print("Initializing LCD")
lcd = i2clcd()
lcd.init()
lcd.print_line('INITIALIZING', line=0, align='CENTER')
lcd.print_line('CAMERA', line=1, align='CENTER')
print("Initializing Camera")
camera = Picamera2()
config = camera.create_still_configuration(main={"size": res})
camera.configure(config)
camera.start()

while True:
    print("Taking picture")

    array = camera.capture_array()
    array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    image = cv2.cvtColor(array, cv2.COLOR_RGB2HSV)


    h, s, v = cv2.split(image)

    hsv_image = [h, s, v]

    print("Finding laser")
    # thresholding
    for i in range(3):
        (t, tmp) = cv2.threshold(hsv_image[i], hsv_max[i], 0, cv2.THRESH_TOZERO_INV)
        (t, hsv_image[i]) = cv2.threshold(tmp, hsv_min[i], 255, cv2.THRESH_BINARY)

    h, s, v = hsv_image

    h = cv2.bitwise_not(h)

    hsv_image = [h, s, v]

    # identify laser
    laser = cv2.bitwise_and(h, v)
    laser = cv2.bitwise_and(s, laser)

    image = cv2.merge(hsv_image)

    center = None

    print("Calculating laser position")
    countours = cv2.findContours(laser, cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)[-2]

    # only proceed if at least one contour was found
    if len(countours) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c = max(countours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        moments = cv2.moments(c)

        if moments["m00"] > 0:
            center = int(moments["m10"] / moments["m00"]), \
                     int(moments["m01"] / moments["m00"])
        else:
            center = int(x), int(y)
        if radius > 10:
            # draw the circle and centroid on the frame,
            cv2.circle(array, (int(x), int(y)), int(radius),
                       (0, 255, 255), 2)
            cv2.circle(array, center, 5, (0, 0, 255), -1)
            # then update the ponter trail
            if previous_position:
                cv2.line(trail, previous_position, center,
                         (255, 255, 255), 2)

        # print(f"trail size: {trail.size}\nframe size: {frame.size}")

        cv2.add(trail, array, array)
        previous_position = center

        print("Calculating distance")
    if center != None:
        print(f"center: {center}")
        rad = (3583 - center[1]) / 1819
        distance = math.tan(rad)*3.96875
        distance = (distance * 100)//100 
        if center[1] > 720 and center[0] > 1010 and center[0] < 1030:
            lcd.print_line('Distance:', line=0, align='CENTER')
            lcd.print_line(f"{distance} cm", line=1, align='CENTER')
        else:
            lcd.print_line('ERROR!', line=0, align='CENTER')
            lcd.print_line('Check lighting!', line=1, align='CENTER')
        sleep(1)

    cv2.imwrite("out.jpg", array)
    cv2.imwrite("laser.jpg", laser)
