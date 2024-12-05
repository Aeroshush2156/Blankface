import os
import glob
import time
import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from flask import Flask, jsonify, render_template, request, redirect, url_for
import threading

# Setup GPIO
#GPIO.cleanup()  # Clean up any previous configurations
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

# Flask setup
app = Flask(__name__)
# Lists for plotting temperature
temperature_data = []
time_data = []
start_time = time.time()

# Function to read raw temperature data from the sensor
def read_temp_raw():
    with open(device_file, 'r') as f:
        valid, temp_line = f.readlines()
    return valid, temp_line

# Function to read and parse the temperature from the sensor
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

# Function to update the temperature label in the GUI
def update_temperature():
    temp = read_temp()  # Read the current temperature
    temperature_label.config(text=f"Temperature: {temp:.2f} °C")  # Update the label
    root.after(1000, update_temperature)  # Schedule this function to run again in 1 second

# Function to update the temperature plot in the GUI
def update_temperature_plot():
    global temperature_data, time_data
    temp = read_temp()

    # Update lists for plotting
    temperature_data.append(temp)
    elapsed_time = time.time() - start_time
    time_data.append(round(elapsed_time / 60.0, 1))  # Store elapsed time in minutes, rounded to 1 decimal place

    # Clear the previous plot
    ax.clear()

    # Plot with improved formatting
    ax.plot(time_data, temperature_data, label='Temperature (°C)', color='blue')
    ax.set_xlabel('Time (minutes)', fontsize=12)  # Set x-label font size
    ax.set_ylabel('Temperature (°C)', fontsize=12)  # Set y-label font size
    ax.set_title('Temperature vs Time', fontsize=14)  # Title font size

    # Control visibility and style of axis ticks
    ax.tick_params(axis='both', direction='in', length=6, width=2)  # Style the ticks

    # Setting y-axis limits
    ax.set_ylim(bottom=0)  # Start y-axis at 0

    # Making x-axis readable
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Show integer values on x-axis
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}'))  # Format x-axis in minutes

    # Add grid and legend
    ax.grid(True)
    ax.legend()

    # Adjusting margins to ensure labels are visible
    plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)

    # Refresh the canvas
    canvas.draw()

    # Schedule the next update of temperature
    root.after(60000, update_temperature_plot)  # Update every minute

# Flask route to render the home page
@app.route('/')
def home():
    current_temp = read_temp()  # Get the current temperature
    return render_template('index.html', temperature=current_temp, target_temperature=target_temperature)  # Render the HTML template

# Flask route to get the current temperature as JSON
@app.route('/api/temperature')
def get_temperature():
    current_temp = read_temp()
    return jsonify({'temperature': current_temp})  # Return temperature as JSON

# Flask route to get the data for plotting as JSON
@app.route('/api/data')  # New endpoint for plotting
def get_plot_data():
    temp = read_temp()

    # Append new readings
    temperature_data.append(temp)
    elapsed_time = time.time() - start_time
    time_data.append(elapsed_time / 60.0)  # Append time in minutes

    return jsonify({'time': time_data, 'temperature': temperature_data})  # Send both time and temperature data

# Flask route to set the target temperature
# Global variable for target temperature
target_temperature = None
@app.route('/set_target_temperature', methods=['POST'])
def set_target_temperature_web():
    target = request.form.get('target_temp')
    set_target_temperature(target)  # Use the merged function
    return redirect(url_for('home'))  # Redirect back to the home page


# Function to run the Flask server
def run_flask():
    app.run(host='0.0.0.0', port=5001)  # Runs Flask on port 5001

# Function to check the system status and update the GUI accordingly
def check_system_status(current_temp):
    target_input = target_temp_entry.get()  # Get the current input from the entry
    if not target_input:  # Check if the entry is empty
        status_label.config(text="Target temperature not set", foreground='orange')
        return

    try:
        target = float(target_input)  # Try to convert to float
    except ValueError:
        status_label.config(text="Invalid target temperature!", foreground='red')
        return

    if isinstance(current_temp, (int, float)):
        if current_temp < target:  # Heating needed
            GPIO.output(HEAT_PIN, GPIO.HIGH)
            GPIO.output(COOL_PIN, GPIO.LOW)
            status_label.config(text=f"System is Heating: {current_temp:.2f}/{target:.2f} °C", foreground='red')
        elif current_temp > target:  # Cooling needed
            GPIO.output(COOL_PIN, GPIO.HIGH)
            GPIO.output(HEAT_PIN, GPIO.LOW)
            status_label.config(text=f"System is Cooling: {current_temp:.2f}/{target:.2f} °C", foreground='blue')
        else:  # System is idle
            GPIO.output(HEAT_PIN, GPIO.LOW)
            GPIO.output(COOL_PIN, GPIO.LOW)
            status_label.config(text="System is Idle", foreground='black')
    else:
        status_label.config(text="Invalid current temperature!", foreground='red')



# Function to set the target temperature and update the system status
def set_target_temperature(target):
    # This function gets called when the button is pressed
    global target_temperature
    try:
        target_temperature = float(target)
        current_temp = read_temp()
        check_system_status(current_temp)

        if current_temp < target_temperature:  # Heating needed
            GPIO.output(HEAT_PIN, GPIO.HIGH)
            GPIO.output(COOL_PIN, GPIO.LOW)
            status_label.config(text=f"System is Heating: {current_temp:.2f}/{target_temperature:.2f} °C", foreground='red')
        elif current_temp > target_temperature:  # Cooling needed
            GPIO.output(COOL_PIN, GPIO.HIGH)
            GPIO.output(HEAT_PIN, GPIO.LOW)
            status_label.config(text=f"System is Cooling: {current_temp:.2f}/{target_temperature:.2f} °C", foreground='blue')
        else:  # System is idle
            GPIO.output(HEAT_PIN, GPIO.LOW)
            GPIO.output(COOL_PIN, GPIO.LOW)
            status_label.config(text="System is Idle", foreground='black')

    except ValueError:
        target_temp_entry.delete(0, tk.END)
        target_temp_entry.insert(0, "Invalid input, please enter a numeric value")
        status_label.config(text="Invalid target temperature!", foreground='red')

# Cleanup GPIO on exit
def on_exit():
    GPIO.cleanup()
    print("GPIO cleanup done.")

# Register the cleanup function to be called on exit
import atexit
atexit.register(on_exit)

# GUI setup
root = tk.Tk()
root.title("Temperature Monitor")

def update_gui_target_temperature():
    if target_temperature is not None:
        target_temp_entry.delete(0, tk.END)
        target_temp_entry.insert(0, str(target_temperature))
    root.after(1000, update_gui_target_temperature)  # Update every second

# Call the function to start updating the GUI
update_gui_target_temperature()

# Start the Flask server in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True  # Ensure the thread exits when the main program exits
flask_thread.start()



fig, ax = plt.subplots(figsize=(5, 3))  # Set figure size
canvas = FigureCanvasTkAgg(fig, master=root)  # Create a canvas to display the plot

# Create a frame for better layout management
frame = ttk.Frame(root, padding="10 10 10 10")
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
# Configure row and column weights
root.columnconfigure(0, weight=1)  # Allow column to expand
root.rowconfigure(0, weight=1)     # Allow row to expand
frame.columnconfigure(0, weight=1)  # Center contents in frame
frame.rowconfigure(0, weight=1)

# Adding the temperature label
temperature_label = ttk.Label(frame, text="Temperature: ---°C")
temperature_label.grid(column=0, row=1, sticky=(tk.N, tk.E, tk.W))

# Entry for the target temperature
target_temp_entry = ttk.Entry(frame)
target_temp_entry.grid(column=0, row=2, sticky=(tk.N, tk.E, tk.W))

# Set Temperature Button
set_temp_button = ttk.Button(frame, text="Set Target Temperature", command=lambda: set_target_temperature(target_temp_entry.get()))
set_temp_button.grid(column=0, row=3, sticky=(tk.N, tk.E, tk.W))# Set Temperature Button

# Status Label
status_label = ttk.Label(frame, text="System Status: Idle", foreground="black")
status_label.grid(column=0, row=4, sticky=(tk.N, tk.E, tk.W))

# Create Plot
fig, ax = plt.subplots(figsize=(5, 3))  # Set the figure size
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(column=0, row=5, sticky=(tk.W, tk.E))  # Use sticky for center alignment

# Update the temperature and start plotting
update_temperature()  # Initial call to start the process
update_temperature_plot()  # Start updating the plot

root.mainloop() # Start the GUI event loop

# Cleanup GPIO on exit
GPIO.cleanup()