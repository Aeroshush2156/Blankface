import os
import glob
import time
import tkinter as tk
from tkinter import ttk

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

# GUI setup
root = tk.Tk()
root.title("Temperature Monitor")

# Adding a frame for better layout management
frame = ttk.Frame(root, padding="10 10 10 10")
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

temperature_label = ttk.Label(frame, text="Temperature: -- °C")
temperature_label.grid(column=1, row=1, sticky=(tk.W, tk.E))

update_temperature()  # Initial call to start temperature updates

root.mainloop()