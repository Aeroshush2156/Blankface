import os
import glob
import time
import logging

# Setup basic logging
logging.basicConfig(filename='temperature.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Initialize the GPIO Pins
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

try:
    while True:
        temperature = read_temp()
        if temperature:
            print(f"Current temperature: {temperature} °C")
            logging.info(f"Temperature reading: {temperature} °C")
            # Very basic sleep interval of 1 minute for readings (customize as needed)
            time.sleep(60)
except KeyboardInterrupt:
    print("Stopped by User")
    logging.info("Temperature reading stopped by user.")
except Exception as e:
    print(f"Error: {str(e)}")
    logging.error(f"Error when trying to read temperature: {str(e)}")