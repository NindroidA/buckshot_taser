import socket
import json
import time
from gpiozero import LED
import threading
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

class ShotReceiver:
    def __init__(self):
        load_dotenv()

        # network settings
        self.port = int(os.getenv('PORT', '5000'))

        # gpio settings
        self.gpio_pin = int(os.getenv('GPIO', '18'))
        self.trigger_duration = float(os.getenv('T_DURATION', '1.0'))

        # states
        self.running = False
        self.total_shots = 0
        self.last_trigger_time = 0

        # initialize gpio
        try:
            self.led = LED(self.gpio_pin)
            logger.info(f"GPIO pin {self.gpio_pin} initialized!")
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            raise

        # create le socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('0.0.0.0', self.port))
            self.sock.settimeout(1.0)
            logger.info(f"UDP socket bound to port {self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize socket: {e}")
            raise

    # triggering gpio pin
    def trigger_gpio(self):
        try:
            logger.debug(f"Triggering GPIO {self.gpio_pin}")
            self.led.on()
            time.sleep(self.trigger_duration)
            self.led.off()
            logger.debug("GPIO trigger complete.")
        except Exception as e:
            logger.error(f"Error during GPIO trigger: {e}")    

    # handling shot detection event
    def handle_shot(self):
        self.total_shots += 1
        current_time = time.time()
        time_since_last = current_time - self.last_trigger_time

        logger.info(f"Shot detected! (Total: {self.total_shots})")

        # start gpio shit in another thread
        threading.Thread(target=self.trigger_gpio).start()
        self.last_trigger_time = current_time

    # stop and cleanup
    def stop(self):  
        self.running = False
        self.led.off()
        self.sock.close()
        logger.info(f"Receiver stopped. Total shots detected: {self.total_shots}") 

    # main loop
    def run(self):
        self.running = True

        logger.info(f"Receiver starting on port {self.port} ...")
        logger.info(f"Using GPIO pin {self.gpio_pin}")

        try:
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    try:
                        message = json.loads(data.decode())
                        if message.get('event') == 'shot_detected':
                            self.handle_shot()
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON data from {addr}")
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            logger.info("\nStopping receiver ...")
        finally:
            self.stop()

def test_gpio():
    gpio_pin = int(os.getenv('GPIO', '18'))
    trigger_duration = float(os.getenv('T_DURATION', '1.0'))

    logger.info("Testing GPIO ...")
    led = LED(gpio_pin)

    try:
        logger.info(f"Turning GPIO {gpio_pin} on for {trigger_duration} seconds")
        led.on()
        time.sleep(trigger_duration)
        led.off()
        logger.info("GPIO test success.")
        return True
    except Exception as e:
        logger.error(f"GPIO test failed: {e}")
        return False
    finally:
        led.off()

def main():
    try:
        load_dotenv()

        print("\nBuckshot Roulette Shot Receiver")
        print("=====================")
        print(f"GPIO Pin: {os.getenv('GPIO', '18')}")
        print(f"Trigger Duration: {os.getenv('T_DURATION', '1.0')}s")
        print(f"Port: {os.getenv('PORT', '5000')}")
        print("\nPress 'ctr+c' to stop the receiver")

        # running startup test
        if test_gpio():
            # we good? then we good :)
            receiver = ShotReceiver()
            receiver.run()
        else:
            logger.error("GPIO test failed. Please check config.")
    except Exception as e:
        logger.error(f"FATAL ERROR YOU BASTARD: {e}")
        raise            
