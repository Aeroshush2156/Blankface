import os
import glob
import time
import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
COOL_PIN = 27
HEAT_PIN = 17
GPIO.setup(COOL_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(HEAT_PIN, GPIO.OUT, initial=GPIO.LOW)

# Setup for DS18B20 temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Set up the location of the sensor in the system
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-7d7c5e1f64ff')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    with open(device_file, 'r') as f:
        valid, temp_line = f.readlines()
    return valid, temp_line

def read_temp():
    valid, temp_line = read_temp_raw()
    while not valid.strip().endswith('YES'):
        time.sleep(0.2)
        valid, temp_line = read_temp_raw()
    equals_pos = temp_line.find('t=')
    if equals_pos != -1:
        temp_string = temp_line[equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def update_temperature():
    temp = read_temp()
    temperature_label.config(text=f"Temperature: {temp:.2f} °C")
    root.after(1000, update_temperature)

def set_target_temperature():
    try:
        target = float(target_temp_entry.get())
        current_temp = read_temp()
        if current_temp < target:  # Need heating
            GPIO.output(HEAT_PIN, GPIO.HIGH)
            GPIO.output(COOL_PIN, GPIO.LOW)
        elif current_temp > target:  # Need cooling
            GPIO.output(COOL_PIN, GPIO.HIGH)
            GPIO.output(HEAT_PIN, GPIO.LOW)
    except ValueError:
        target_temp_entry.delete(0, tk.END)
        target_temp_entry.insert(0, "Invalid input, please enter a numeric value")

# GUI setup
root = tk.Tk()
root.title("Temperature Monitor")

frame = ttk.Frame(root, padding="10 10 10 10")
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

temperature_label = ttk.Label(frame, text="Temperature: -- °C")
temperature_label.grid(column=1, row=1, sticky=(tk.W, tk.E))

target_temp_entry = ttk.Entry(frame)
target_temp_entry.grid(column=1, row=2)

set_temp_button = ttk.Button(frame, text="Set Target Temperature", command=set_target_temperature)
set_temp_button.grid(column=1, row=3)

update_temperature()
root.mainloop()