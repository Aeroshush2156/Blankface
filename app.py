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
"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"
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
    check_system_status(temp)
    root.after(1000, update_temperature)

def check_system_status(current_temp):
    target = float(target_temp_entry.get()) if target_temp_entry.get() else None

    if target is not None and isinstance(current_temp, (int, float)):
        if current_temp < target:  # Heating needed
            GPIO.output(HEAT_PIN, GPIO.HIGH)
            GPIO.output(COOL_PIN, GPIO.LOW)
            status_label.config(text=f"System is Heating: {current_temp:.2f}/{target:.2f} °C", fg='red')
        elif current_temp > target:  # Cooling needed
            GPIO.output(COOL_PIN, GPIO.HIGH)
            GPIO.output(HEAT_PIN, GPIO.LOW)
            status_label.config(text=f"System is Cooling: {current_temp:.2f}/{target:.2f} °C", fg='blue')
        else:  # System is idle
            GPIO.output(HEAT_PIN, GPIO.LOW)
            GPIO.output(COOL_PIN, GPIO.LOW)
            status_label.config(text="System is Idle", fg='black')
    else:
        status_label.config(text="Invalid target temperature!", fg='red')
def set_target_temperature():
    try:
        target = float(target_temp_entry.get())
        check_system_status(read_temp())  # Check the system status with the current temperature.
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

# Status label to show current system status
status_label = ttk.Label(frame, text="System Status: Idle", foreground="black")
status_label.grid(column=1, row=4, sticky=(tk.W, tk.E))

update_temperature()
root.mainloop()

# Cleanup GPIO on exit
GPIO.cleanup()