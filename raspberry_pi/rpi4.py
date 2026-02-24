import subprocess
import socket
from adafruit_pca9685 import PCA9685
import busio
import board
import threading
import pins
import donkeycar as dk
from donkeycar.parts.actuator import PWMSteering, PWMThrottle, PulseController



server_ip = '192.168.1.231'
UDP_PORT = 5000

TCP_PORT = 6000

cfg = dk.load_config()

dt = cfg.PWM_STEERING_THROTTLE

steering_controller = PulseController(
    pwm_pin=pins.pwm_pin_by_id(dt["PWM_STEERING_PIN"]),
    pwm_scale=dt["PWM_STEERING_SCALE"],
    pwm_inverted=dt["PWM_STEERING_INVERTED"]
)

steering = PWMSteering(
    controller=steering_controller,
    left_pulse=dt["STEERING_LEFT_PWM"],
    right_pulse=dt["STEERING_RIGHT_PWM"]
)

throttle_controller = PulseController(
    pwm_pin=pins.pwm_pin_by_id(dt["PWM_THROTTLE_PIN"]),
    pwm_scale=dt["PWM_THROTTLE_SCALE"],
    pwm_inverted=dt["PWM_THROTTLE_INVERTED"]
)

throttle = PWMThrottle(
    controller = throttle_controller,
    max_pulse = dt["THROTTLE_FORWARD_PWM"],
    zero_pulse = dt["THROTTLE_STOPPED_PWM"],
    min_pulse = dt["THROTTLE_REVERSE_PWM"]
)


def start_udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))

    print(f"UDP Server listening on port {UDP_PORT}...")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            data = data.decode("utf-8").strip()

            if not data:
                continue

            try:
                steering_value, throttle_value = map(float, data.split(","))
            except ValueError:
                print(f"Invalid data received: {data}")
                continue

            steering.run(steering_value)
            throttle.run(throttle_value)

        except (socket.error, KeyboardInterrupt):
            print("Socket error or interrupted. Shutting down...")
            break

    sock.close()

#original width 640 height 480
def start_video_stream():
    cmd=f"libcamera-vid -t 0 --width 160 --height 120 --inline --hflip --vflip --output udp://{server_ip}:{UDP_port}"
    
    print("Starting libcamera-vid stream...")
    subprocess.Popen(cmd, shell=True)
    print("Video stream started")

threading.Thread(target=start_video_stream, daemon=True).start()
start_udp_server()

