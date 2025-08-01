####################################################################################################
#
# PNFLtest - 7/30/2025 - Tyler Frischknecht
# Pennathur Nanofluidics Lab Keithley Test Commands
TEST_VERSION = "   Test: 1.2.4"
#
####################################################################################################
# Import Libraries
import threading # for thread release and preventing other threads from running when locked
from helper.pnflmail import sendEmail
from helper.pnflfile import makeAllFiles
import matplotlib.ticker as ticker
import matplotlib.pyplot as plot
import warnings
import pyvisa
import numpy
import time
import datetime  
import os
#
####################################################################################################
# Global Variables
#
# Moved to run_test
####################################################################################################
#
def runTest(ALL_GPIB_ADDRESSES, VOLTAGE, TEST_TIME, EMAILS, TEST_NAME, TEST_INFO, version, GRAPH=True): # For older versions
    run_test(ALL_GPIB_ADDRESSES, VOLTAGE, TEST_TIME, EMAILS, TEST_NAME, TEST_INFO, GRAPH, version)
def run_test(ALL_GPIB_ADDRESSES, VOLTAGE, TEST_TIME, EMAILS, TEST_NAME, TEST_INFO, GRAPH, version):
    # Important variables:
    IMAGE_PATH = None
    TIMESTAMP = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    if __name__ == "__main__":
        IMAGE_PATH = os.path.join('...', 'data', f"data{TIMESTAMP}.png")
    else:
        IMAGE_PATH = os.path.join('helper', 'data', f"data{TIMESTAMP}.png")
    version += TEST_VERSION
    test_success = False
    # Test:
    try:
        ALL_KEITHLEYS = connect_to_keithley(ALL_GPIB_ADDRESSES)
        KEITHLEY_LOCKS = [threading.Lock() for _ in ALL_KEITHLEYS]
        CANCEL_QUERY_EVENTS = [threading.Event() for _ in ALL_KEITHLEYS]
        print("Setting limits.")
        setLimits(ALL_KEITHLEYS, VOLTAGE)
        data = source_and_read(ALL_KEITHLEYS, VOLTAGE, TEST_TIME, GRAPH, KEITHLEY_LOCKS, CANCEL_QUERY_EVENTS, TIMESTAMP, IMAGE_PATH)
        test_success = True
    except pyvisa.VisaIOError as e:
        print(f"VisaIOError: {e}")
        print(f"Sorry about that, please run the test again!")
        exit(1)
    except Exception as e:
        print(f"Exception: {e}")
        print(f"Sorry about that, please run the test again!")
        exit(1)
    finally:
        for keithley in ALL_KEITHLEYS:
            try:
                keithley.write("OUTP 0")
                keithley.close()
                print("Connection with Keithley terminated.")
            except Exception as e:
                print(f"Failed to close connection with Keithley - {e}")
    if test_success == True:
        # put data into file here!
        version += makeAllFiles(data, TIMESTAMP, len(ALL_KEITHLEYS))
        sendEmail(EMAILS, TIMESTAMP, f"({VOLTAGE} V) "+ TEST_NAME, TEST_INFO, GRAPH, version)
#
####################################################################################################
# Connects to Keithley and returns keithley as object to write to with pyvisa
def connect_to_keithley(ALL_GPIB_ADDRESSES):
    desired_keithley_ports = []
    all_keithleys = []
   
    rm = pyvisa.ResourceManager() # This will manage the connection
    all_connected_ports = rm.list_resources()
   
    for port in all_connected_ports:
        if port[0:4] == 'GPIB' and int(port[7:9]) in ALL_GPIB_ADDRESSES:
            print("Found port: ", port)
            desired_keithley_ports.append(port)
           
    for port in desired_keithley_ports:
        print("Attempting to connect to port", port)
        keithley = rm.open_resource(port)  # Open connection to the Keithley
        print("Connected to Keithley Model:", keithley.query("*IDN?"), end='')
        all_keithleys.append(keithley)
        time.sleep(0.25)

    print(f"Connected to {len(all_keithleys)} Keithleys.")
   
    return(all_keithleys)
#
####################################################################################################
#
def setLimits(ALL_KEITHLEYS, VOLTAGE):
    for keithley in ALL_KEITHLEYS:
        # Resets all the sad stuff that couldve been there before:
        keithley.write("*CLS")
        keithley.write("*RST")
        keithley.write("STAT:PRES;*CLS")
        # Enable Status Byte
        keithley.write("STAT:MEAS:ENAB 512")
        keithley.write("*SRE 0")
        # Enable VOLTAGE and Current Limit
        keithley.write("SOUR:VOLT:LIM:STAT 1")      # Turns VOLTAGE limiting on
        # Applies numerical limits
        keithley.write("SOUR:VOLT:LIM " + str(abs(max(VOLTAGE))+5))
        keithley.write("SENS:FUNC 'CURR:DC'")       # Sets the current measuring value to current
        keithley.write("SENS:CURR:RANG:AUTO 1")     # Enables auto range for current
        keithley.write("SENS:CURR:DIG 6")           # Sets float decimal digits to max (6)
        keithley.write("SYST:ZCH 1")                # Turns zero check on
        keithley.write("SYST:ZCH 0")                # Turns zero check off
        keithley.write("SYST:ZCOR 1")               # Turns zero correction on
        # Set trigger delay between automated triggers:
        keithley.write("TRIG:DEL 0.44") # Adjusted ~0.5s between buffer readings'
#
####################################################################################################
#
def find_status(keithley, KEITHLEY_NUMBER):
    polling_value = keithley.read_stb()
    if polling_value % 2 == 0:
        return True
    print(f"Buffer Full in Keithley #{KEITHLEY_NUMBER + 1}")
    return False
#
####################################################################################################
#
def safe_query(keithley, command, lock, event):
    result = None
    lock.acquire()
    try:
        if not event.is_set():
            result = keithley.query(command)
    finally:
        lock.release()
    return result
#
####################################################################################################
def keithley_test_thread(master_data, keithley, VOLTAGE, TEST_TIME, KEITHLEY_LOCK, CANCEL_QUERY_EVENT, KEITHLEY_NUMBER):
    owns_lock = False
    self_data = []
    #
    for v, t in zip(VOLTAGE, TEST_TIME):
        total_points = int(t * 2 * 60)
        testing_status = True
        buffer_size = total_points
        if total_points > 3600: # If test time longer than 30 minutes, clear the buffer after 30 minutes then continue test.
            buffer_size = 3600
            #
        keithley.write("TRAC:CLE")  # Clears Buffer
        keithley.write(f"TRIG:COUN {buffer_size}") # Sets trigger count to buffer size
        keithley.write(f"TRAC:POIN {buffer_size}") # Sets amount of points collected in the buffer to buffer size
        keithley.write("TRAC:FEED:CONT NEXT")   # Sets buffer to recieve readings (must be below the above two commands)
        #
        keithley.write("SOUR:VOLT " + str(v))   # Sets source VOLTAGE to VOLTAGE in list
        keithley.write("OUTP 1")    # Turns on VOLTAGE output
        keithley.write("INIT")
        #
        print(f"Started test {v}V test for {t}min on Keithley #{KEITHLEY_NUMBER + 1}")
        if owns_lock == True:
            KEITHLEY_LOCK.release()
            owns_lock = False
        #
        while total_points > 0:
            testing_status = find_status(keithley, KEITHLEY_NUMBER)
            try:
                if testing_status: # If buffer not full
                    time.sleep(1)
                    #    
                else: # If buffer full
                    KEITHLEY_LOCK.acquire()
                    try:
                        owns_lock = True
                        keithley.write("*WAI") # Ensures that the keithley finishes its buffer cycle before attempting to read it all.
                        buffer_data = keithley.query("TRAC:DATA?").strip() + ","
                        self_data.append(buffer_data) # Reads from the buffer
                        keithley.write("TRAC:CLE")  # Clears Buffer
                        keithley.write("*CLS")      # Clears Status Byte
                        #
                        total_points -= buffer_size # Subtract the amount of points gathered from the total
                        if total_points <= 0:   # If no more points to gather return.
                            continue
                        elif total_points < 3600:   # If less than 3600 points to collect, set amount left to collect as such
                            buffer_size = total_points
                        keithley.write(f"TRIG:COUN {buffer_size}")
                        keithley.write(f"TRAC:POIN {buffer_size}")
                        keithley.write("TRAC:FEED:CONT NEXT")   # Sets buffer to recieve readings again (must be below the above two commands)
                        #
                        time.sleep(0.25)
                        #
                        keithley.write("INIT")  # Starts next test cycle
                        print(f"Continuing test cycle after buffer reading on Keithley #{KEITHLEY_NUMBER}")
                        time.sleep(1)
                        KEITHLEY_LOCK.release()
                        owns_lock = False
                    #
                    except Exception as e:
                        print("{threading.current_thread().name} on lock {id(KEITHLEY_LOCK)} experienced an error:")
                        print(e)
            except Exception as e:
                print("Error somewhere within the outermost try in the while total_points > 0 loop:")
                print(e)
        #
        keithley.write("OUTP 0")
        time.sleep(0.25)
    CANCEL_QUERY_EVENT.set()
    if owns_lock == True:
        KEITHLEY_LOCK.release()
        owns_lock = False
    #
    master_data[KEITHLEY_NUMBER] = self_data      
#
####################################################################################################
#
def get_gpib_address(keithley):
    try:
        return keithley.resource_name.split("::")[1]
    except Exception as e:
        print(f"Failed to get GPIB address: {e}")
        return "X"
#
####################################################################################################
# Graph Functions to replace Graph Thread. MATPLOTLIB is a greedy little rat that wants to hoard the main thread.
def graph_setup(ALL_KEITHLEYS, VOLTAGE, TIMESTAMP):
    NUM_PLOTS = len(ALL_KEITHLEYS)
    #
    plot.ion() # turns on interactive mode
    #
    fig, axes = plot.subplots(NUM_PLOTS, 1, figsize=(8, 2 * NUM_PLOTS))
    if NUM_PLOTS == 1:
        axes = [axes]  # make iterable
    #
    fig.suptitle(f"{TIMESTAMP}  Keithley Test Data at: " + ", ".join(f"{v}V" for v in VOLTAGE))
    #
    lines = []
    x_data = []
    y_data = []
    # Setup all data selections for data
    for ax in axes:
        line, = ax.plot([], [])  # empty line
        lines.append(line)
        x_data.append([])
        y_data.append([])
    # Set titles for each subplot in the window
    for index, ax in enumerate(axes):
        gpib_address = get_gpib_address(ALL_KEITHLEYS[index])
        ax.set_title(f"Keithley GPIB: {gpib_address}")
        formatter = ticker.FormatStrFormatter('%.4e')
        ax.yaxis.set_major_formatter(formatter)
    # Set vertical spacing between graphs so text doesn't overlap
    fig.subplots_adjust(hspace=0.5)
    # Draw initial canvas so window appears and stays open
    fig.canvas.draw()
    fig.canvas.flush_events()
    # When a test cycle completes, keithley returns time from start of test, not from overall start. this fixes that
    additional_time = [0 for _ in ALL_KEITHLEYS]
    last_time_reading = [0 for _ in ALL_KEITHLEYS]
    # Returns all plot pieces as a dict for easier modification in the future
    return {
        'fig': fig,
        'axes': axes,
        'lines': lines,
        'x_data': x_data,
        'y_data': y_data,
        'additional_time': additional_time,
        'last_time_reading': last_time_reading
    }

def graph_update(ALL_KEITHLEYS, KEITHLEY_LOCKS, CANCEL_QUERY_EVENTS, plot_dict):
    for index, keithley in enumerate(ALL_KEITHLEYS):
        try:
            response = (safe_query(keithley, "FETCH?", KEITHLEY_LOCKS[index], CANCEL_QUERY_EVENTS[index])).split(',')[0:2]
        except Exception:
            continue
        if response == None:
            continue

        time_reading = float(response[1][:-4])
        if time_reading < plot_dict['last_time_reading'][index]:
            plot_dict['additional_time'][index] += plot_dict['last_time_reading'][index]
        plot_dict['last_time_reading'][index] = time_reading

        plot_dict['x_data'][index].append(time_reading + plot_dict['additional_time'][index])
        plot_dict['y_data'][index].append(abs(float(response[0][:-4])))

        line = plot_dict['lines'][index]
        line.set_xdata(plot_dict['x_data'][index])
        line.set_ydata(plot_dict['y_data'][index])

        ax = plot_dict['axes'][index]
        ax.relim()
        ax.autoscale_view()

    plot_dict['fig'].canvas.draw_idle()
    plot_dict['fig'].canvas.flush_events()

def graph_close(plot_dict, IMAGE_PATH):
    plot.ioff()
    if plot_dict and plot_dict['fig']:
        if IMAGE_PATH:
            plot_dict['fig'].savefig(IMAGE_PATH)
        plot.close(plot_dict['fig'])
#
####################################################################################################
#
def clean_data(dataset):
    time_offset = 0.0
    all_readings = []

    for buffer_cycle in dataset:
        readings = buffer_cycle.split("rdng#,")
        # readings should now be list of strings, each one looks like: "+000.1887E-12NADC,+0000001.192989secs,+00001",
        readings = [r for r in readings if r.strip()]
        # readings same as above but empty strings removed
        for r in readings:
            try:
                line_values = r.split(",")
                # line_values becomes line r from readings split into three strings: ["+000.1887E-12NADC", "+0000001.192989secs", "+00001"]
                keithley_current_str = line_values[0]
                # string for current(amps) should be assigned to current_string: "+000.1887E-12NADC"
                time_str = line_values[1]
                # string for time(secs) should be assigned to time_str: "+0000001.192989secs"
                keithley_time_float = float(time_str.replace("secs", ""))
                # time_float takes time value and turns into a float: 1.192989
                continuous_time = keithley_time_float + time_offset
                # continuous_time takes time_offset from before and applies it: 11.192989

                clean_current = keithley_current_str.replace("NADC", "").lstrip("+-")
                # clean_current becomes cleaned string without NADC or sign: "000.1887E-12"
                formatted = f"{clean_current}, {continuous_time:.6f}"
                # formatted string becomes clean data string: "000.1887E-12, 11.192989"
                all_readings.append(formatted)
                # formatted string appended to all_readings
            except Exception as e:
                print(f"Skipping bad reading: {r} ({e})")

        if all_readings:
            last_time_str = all_readings[-1].split(", ")[1]
            # When buffer cycle completely formatted, stores last buffer time value to offset next cycle
            time_offset = float(last_time_str) + 0.5

    return all_readings
#
####################################################################################################
#
def merge_clean_data(cleaned_outputs):
    NUM_READINGS = len(cleaned_outputs[0])
    merged_data = []

    for index in range(NUM_READINGS):
        row = [str(index+1)]
        for keithley_output in cleaned_outputs:
            keithley_current, keithley_timestamp = keithley_output[index].split(',')
            row.append(keithley_current)
            row.append(keithley_timestamp)
        merged_data.append(row)

    return merged_data
#
####################################################################################################
#
def source_and_read(ALL_KEITHLEYS, VOLTAGE, TEST_TIME, GRAPH, KEITHLEY_LOCKS, CANCEL_QUERY_EVENTS, TIMESTAMP, IMAGE_PATH):
    master_data = [None] * len(ALL_KEITHLEYS)
   
    threads = []
    for index, keithley in enumerate(ALL_KEITHLEYS): # Allocates spaces for all data slots required per Keithley
        keithley_thread = threading.Thread(target=keithley_test_thread, args=(master_data, keithley, VOLTAGE, TEST_TIME, KEITHLEY_LOCKS[index], CANCEL_QUERY_EVENTS[index], index))
        keithley_thread.start()
        threads.append(keithley_thread)

    if GRAPH:
        plot_dict = graph_setup(ALL_KEITHLEYS, VOLTAGE, TIMESTAMP)
        # Handles Graphing on Main Thread:
        while all(t.is_alive() for t in threads):
            graph_update(ALL_KEITHLEYS, KEITHLEY_LOCKS, CANCEL_QUERY_EVENTS, plot_dict)
            time.sleep(1)
        graph_close(plot_dict, IMAGE_PATH)

    # Awaits all tasks
    for thread in threads:
        thread.join()

    print("All tests complete!")

    # Takes raw buffer data and turns it into something useful for .csv and .xlsx exporting
    clean_data_list = []
    for index, individual_keithley_dataset in enumerate(master_data):
        clean_data_list.append(clean_data(individual_keithley_dataset))

    merged_data = merge_clean_data(clean_data_list)
   
    return merged_data
#
####################################################################################################
