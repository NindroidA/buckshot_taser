import cv2
import numpy as np
import time
from PIL import ImageGrab
import socket
import json
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BigBrother:
    def __init__(self):
        load_dotenv()

        # network settings
        self.raspi_ip = os.getenv('RASPI_IP', '192.168.1.100')
        self.port = int(os.getenv('PORT', '5000'))

        # detection settings
        self.roi = {
            'x1': int(os.getenv('ROI_X1', '400')),
            'y1': int(os.getenv("ROI_Y1", '300')),
            'x2': int(os.getenv('ROI_X2', '880')),
            'y2': int(os.getenv('ROI_Y2', '600'))
        }

        self.red_threshold = int(os.getenv('RED_THRESH', '1000'))
        self.cooldown = float(os.getenv('COOLDOWN', '2.0'))

        # color range for blud
        self.lower_red = np.array([0, 120, 70])
        self.upper_red = np.array([10, 255, 255])

        # states
        self.running = False
        self.calibration = False
        
        # socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info(f"Big Brother initalized with ROI: {self.roi}")

    # send shot data to raspi
    def notify_raspi(self):
        try:
            message = json.dumps({
                "event": "shot_detected",
                "timestamp": time.time()
            })
            self.sock.sendto(message.encode(), (self.raspi_ip, self.port))
            logger.info(f"Data sent to Raspberry Pi!")
        except Exception as e:
            logger.error(f"Failed to send data: {e}")

    # detect if you got shot
    def detect_shot(self, frame):
        try:
            # display area we looking at
            roi = frame[self.roi['y1']:self.roi['y2'],
                        self.roi['x1']:self.roi['x2']]
            
            # convert to HSV
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # mask for red
            mask = cv2.inRange(hsv, self.lower_red, self.upper_red)

            # count red pixels
            red_pixel_count = np.sum(mask > 0)
            if self.calibration:
                logger.debug(f"Red pixel count: {red_pixel_count}")

            return red_pixel_count > self.red_threshold
        except Exception as e:
            logger.error(f"Error in shot detection: {e}")
            return False

    # capture game screen
    def capture_screen(self):
        try:
            screen = np.array(ImageGrab.grab())
            return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None
        
    # toggle calibration mode
    def toggle_calibration(self):
        self.calibration = not self.calibration
        logger.info(f"Calibration mode {'enabled' if self.calibration else 'disabled'}")

    # stop program and clean up
    def stop(self):
        self.running = False
        self.sock.close()
        cv2.destroyAllWindows()
        logger.info("Big Brother has stopped!")

    # main loop
    def run(self):
        self.running = True
        last_trigger_time = 0

        logger.info("Staring BIG BOTHER MWAHAHA ...")
        logger.info(f"Sending pi data to {self.raspi_ip}:{self.port}")

        try:
            while self.running:
                frame = self.capture_screen()
                if frame is None:
                    continue

                current_time = time.time()

                if self.detect_shot(frame):
                    if current_time - last_trigger_time > self.cooldown:
                        logger.info("Shot detected! Sending pi data ...")
                        self.notify_raspi()
                        last_trigger_time = current_time

                # show monitored frame if in calibration mode
                if self.calibration:
                    debug_frame = frame.copy()
                    cv2.rectangle(debug_frame,
                                  (self.roi['x1'], self.roi['y1'])
                                  (self.roi['x2'], self.roi['y2']),
                                  (0, 255, 0), 2)
                    cv2.imshow('Debug View', debug_frame)    

                    # check for keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('c'):
                        self.toggle_calibration()

                # delay to reduce CPU usage
                time.sleep(0.3)
        except KeyboardInterrupt:
            logger.info("\nStopping Big Brother ...")
        finally:
            self.stop()                

def main():
    try:
        # create and run Big Brother
        detector = BigBrother()

        # print instructions
        print("\nBuckshot Roulette Big Brother")
        print("===============================")
        print("Press 'c' to toggle calibration mode")
        print("Press 'q' to quit")
        print("Press 'ctrl+c' to stop Big Brother")

        # run Big Brother
        detector.run()
    except Exception as e:
        logger.error(f"FATAL ERROR YOU BASTARD: {e}")
        raise

main()            
