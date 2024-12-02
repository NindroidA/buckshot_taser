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
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BigBrother:
    def __init__(self):
        load_dotenv()

        # network settings
        self.raspi_ip = os.getenv('RASPI_IP', '192.168.1.100')
        self.port = int(os.getenv('PORT', '5000'))

        # detection settings
        self.black_threshold = int(os.getenv('BLACK_THRESH', '30'))
        self.black_percentage_threshold = float(os.getenv('BLACK_PERCENT_THRESH', '0.95'))
        self.cooldown = float(os.getenv('COOLDOWN', '2.0'))

        # states
        self.running = False
        self.calibration = False
        
        # socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info(f"Big Brother initalized.")

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
            # convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # count dark pixels
            dark_pixels = np.sum(gray < self.black_threshold)
            total_pixels = gray.size

            # calculate dark pixel percentage
            dark_percentage = dark_pixels / total_pixels

            if self.calibration:
                logger.debug(f"Dark pixel percent: {dark_percentage:.2%}")
            return dark_percentage > self.black_percentage_threshold    
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
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    dark_pixels = np.sum(gray < self.black_threshold)
                    total_pixels = gray.size
                    dark_percentage = dark_pixels / total_pixels
                    debug_frame = frame.copy()
                    cv2.putText(
                        debug_frame,
                        f"Dark pixels: {dark_percentage:.1%}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )
                    cv2.imshow('Debug View', debug_frame)    

                    # check for keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('c'):
                        self.toggle_calibration()

                # delay to reduce CPU usage
                time.sleep(0.2)
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
        # these two don't work atm cause im dumb dumb but dont wanna fix it rn :3
        #print("Press 'c' to toggle calibration mode")
        #print("Press 'q' to quit")
        print("Press 'ctrl+c' to stop Big Brother")

        # run Big Brother
        detector.run()
    except Exception as e:
        logger.error(f"FATAL ERROR YOU BASTARD: {e}")
        raise

main()            
