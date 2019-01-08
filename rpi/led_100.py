import RPi.GPIO as gpio

led_pin = 18

gpio.setwarnings(False)
gpio.setmode(gpio.BCM)
gpio.setup(led_pin, gpio.OUT)
pwm_led = gpio.PWM(led_pin, 1500)
pwm_led.start(0)

while True:
    duty_s = input("Enter Brightness (0 to 100):")
    duty = int(duty_s)
    pwm_led.ChangeDutyCycle(duty)
