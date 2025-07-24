####################################################################################################
#
# PNFLtest - 7/24/2025 - Tyler Frischknecht
# Pennathur Nanofluidics Lab Keithley Test Commands
VERSION = "   TEST: 1.2.0"
#
####################################################################################################
# Import Libraries
import asyncio # For running multiple threads at once.
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
imagePath = None
timestamp = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S") 
if __name__ == "__main__":
    imagePath = os.path.join('...', 'data', f"data{timestamp}.png")
else:
    imagePath = os.path.join('helper', 'data', f"data{timestamp}.png")
#
####################################################################################################
#
def runTest(allGPIB, voltage, testTime, emails, name, info, version):
    version += VERSION
    testSuccess = False
    try:
        allKeithleys = connectToKeithley(allGPIB)
        print("Setting limits.")
        setLimits(allKeithleys, voltage)
        data = asyncio.run(sourceAndRead(allKeithleys, voltage, testTime))
        testSuccess = True
    except pyvisa.VisaIOError as e:
        print(f"VisaIOError: {e}")
        print(f"Sorry about that, please run the test again!")
        exit(1)
    except Exception as e:
        print(f"Exception: {e}")
        print(f"Sorry about that, please run the test again!")
        exit(1)
    finally:
        for keithley in allKeithleys:
            try:
                keithley.close()
                print("Connection with Keithley terminated.")
            except Exception as e:
                print(f"Failed to close connection with Keithley - {e}")
    if testSuccess == True:
        # put data into file here!
        version += makeAllFiles(data, timestamp, len(allKeithleys))
        sendEmail(emails, timestamp, f"({voltage} V) "+ name, info, version)
#
####################################################################################################
# Connects to Keithley and returns keithley as object to write to with pyvisa
def connectToKeithley(allGPIB):
    desiredKeithleyPorts = []
    allKeithleys = []
    
    rm = pyvisa.ResourceManager() # This will manage the connection
    allConnectedPorts = rm.list_resources()
    
    for port in allConnectedPorts:
        if port[0:4] == 'GPIB' and int(port[7:9]) in allGPIB:
            print("Found port: ", port)
            desiredKeithleyPorts.append(port)
            
    for port in desiredKeithleyPorts:
        print("Attempting to connect to port", port)
        keithley = rm.open_resource(port)  # Open connection to the Keithley
        print("Connected to Keithley Model:", keithley.query("*IDN?"), end='')
        allKeithleys.append(keithley)
        time.sleep(0.25)
    return(allKeithleys)
#
####################################################################################################
#
def setLimits(allKeithleys, sourceVoltage):
    for keithley in allKeithleys:
        # Resets all the sad stuff that couldve been there before:
        keithley.write("*CLS")
        keithley.write("*RST")
        keithley.write("STAT:PRES;*CLS")
        # Enable Status Byte
        keithley.write("STAT:MEAS:ENAB 512")
        keithley.write("*SRE 1")
        # Enable Voltage and Current Limit
        keithley.write("SOUR:VOLT:LIM:STAT 1")      # Turns voltage limiting on
        # Applies numerical limits
        keithley.write("SOUR:VOLT:LIM " + str(abs(max(sourceVoltage))+5))
        keithley.write("SENS:FUNC 'CURR:DC'")       # Sets the current measuring value to current
        keithley.write("SENS:CURR:RANG:AUTO 1")     # Enables auto range for current
        keithley.write("SENS:CURR:DIG 6")           # Sets float decimal digits to max (6)
        keithley.write("SYST:ZCH 1")                # Turns zero check on
        keithley.write("SYST:ZCH 0")                # Turns zero check off
        keithley.write("SYST:ZCOR 1")               # Turns zero correction on
        # Set trigger delay between automated triggers:
        keithley.write("TRIG:DEL 0.45") # Adjusted ~0.5s between buffer readings'
#
####################################################################################################
#
async def findStatus(keithley, keithley_number):
    polling_value = keithley.read_stb()
    if polling_value % 2 == 0:
        return True
    print(f"Buffer Full in Keithley #{keithley_number}")
    return False
#
####################################################################################################
#
async def keithleyTestThread(keithley, voltage, testTime, keithley_number):
    SELF_DATA = []
    #
    for v, t in zip(voltage, testTime):
        TOTAL_POINTS = t * 2 * 60
        TESTING_STATUS = True
        BUFFER_SIZE = TOTAL_POINTS
        if TOTAL_POINTS > 3600: # If test time longer than 30 minutes, clear the buffer after 30 minutes then continue test.
            BUFFER_SIZE = 3600
            #
        keithley.write("TRAC:CLE")  # Clears Buffer
        keithley.write(f"TRIG:COUN {BUFFER_SIZE}") # Sets trigger count to buffer size
        keithley.write(f"TRAC:POIN {BUFFER_SIZE}") # Sets amount of points collected in the buffer to buffer size
        keithley.write("TRAC:FEED:CONT NEXT")   # Sets buffer to recieve readings (must be below the above two commands)
        #
        keithley.write("SOUR:VOLT " + str(v))   # Sets source voltage to voltage in list
        keithley.write("OUTP 1")    # Turns on voltage output
        keithley.write("INIT")
        #
        print(f"Started test {v}V test for {t}min on Keithley #{keithley_number}")
        #
        while TOTAL_POINTS > 0:
            TESTING_STATUS = await findStatus(keithley, keithley_number)
            try:
                if TESTING_STATUS: # If buffer not full
                    await asyncio.sleep(1)
                    #    
                else: # If buffer full
                    SELF_DATA.append(keithley.query("TRAC:DATA?").strip() + ",") # Reads from the buffer
                    keithley.write("TRAC:CLE")  # Clears Buffer
                    keithley.write("*CLS")      # Clears Status Byte
                    # 
                    TOTAL_POINTS -= BUFFER_SIZE # Subtract the amount of points gathered from the total
                    if TOTAL_POINTS <= 0:   # If no more points to gather return.
                        break
                    elif TOTAL_POINTS < 3600:   # If less than 3600 points to collect, set amount left to collect as such
                        keithley.write(f"TRIG:COUN {TOTAL_POINTS}")
                        keithley.write(f"TRAC:POIN {TOTAL_POINTS}")
                        keithley.write("TRAC:FEED:CONT NEXT")   # Sets buffer to recieve readings again (must be below the above two commands)
                        #
                    await asyncio.sleep(0.25)
                    #
                    keithley.write("INIT")  # Starts next test cycle
                    print(f"Started next test cycle on Keithley #{keithley_number}")
                    #
            except KeyboardInterrupt:
                print("Broken by User.")
                if keithley:
                    keithley.write("OUTP 0")
                    keithley.write("ABOR")
                    keithley.close()
        keithley.write("OUTP 0")
        await asyncio.sleep(0.25)
    #
    return SELF_DATA
            
#
####################################################################################################
#
async def get_gpib_address(keithley):
    try:
        return keithley.resource_name.split("::")[1]
    except Exception as e:
        print(f"Failed to get GPIB address: {e}")
        return "X"
#
####################################################################################################
#
async def graphThread(all_keithleys, voltage):
    num_plots = len(all_keithleys)
    
    plot.ion()  # turn on interactive mode

    fig, axes = plot.subplots(num_plots, 1, figsize=(8, 2 * num_plots))
    if num_plots == 1:
        axes = [axes]  # make iterable

    # Set title of overall window
    fig.suptitle(f"{timestamp}  Keithley Test Data at: " + ", ".join(f"{v}V" for v in voltage))

    lines = []
    x_data = []
    y_data = []
    for ax in axes:
        line, = ax.plot([], [])  # empty line
        lines.append(line)
        x_data.append([])
        y_data.append([])

    # Set titles for each subplot in the window
    for i, ax in enumerate(axes):
        gpib_address = await get_gpib_address(all_keithleys[i])
        ax.set_title(f"Keithley GPIB: {gpib_address}")
        formatter = ticker.FormatStrFormatter('%.4e')
        ax.yaxis.set_major_formatter(formatter)

    # Set vertical spacing between graphs so text doesn't overlap
    fig.subplots_adjust(hspace=0.5)

    # Draw initial canvas so window appears and stays open
    fig.canvas.draw()
    fig.canvas.flush_events()

    # When a test cycle completes, keithley returns time from start of test, not from overall start. this fixes that
    additional_time = [0 for _ in all_keithleys]
    last_time_reading = [0 for _ in all_keithleys]

    try:
        while True:
            for i, keithley in enumerate(all_keithleys):
                # Collect data from keithley
                try:
                    response = keithley.query("FETCH?").split(',')[0:2]
                except Exception as e:
                    continue
                
                # Append data to dataset
                time_reading = float(response[1][:-4])
                if time_reading < last_time_reading[i]:
                    additional_time[i] += last_time_reading[i]
                last_time_reading[i] = time_reading
                x_data[i].append(time_reading + additional_time[i]) # Time
                y_data[i].append(float(response[0][:-4])) # Current

                # Update graph
                lines[i].set_xdata(x_data[i])
                lines[i].set_ydata(y_data[i])
                axes[i].relim() # Recalculates autoscale limits
                axes[i].autoscale_view() # Applies autoscale limits

            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            plot.pause(1)
            await asyncio.sleep(1)  # just wait, no changes yet
    except asyncio.CancelledError:
        if fig:
            plot.ioff() # Disables interactive mode                                                    
            plot.savefig(imagePath)
    except Exception as error:
        print("Error in Plotting Thread: ", error)  
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
                current_str = line_values[0]
                # string for current(amps) should be assigned to current_string: "+000.1887E-12NADC"
                time_str = line_values[1]
                # string for time(secs) should be assigned to time_str: "+0000001.192989secs"
                time_float = float(time_str.replace("secs", ""))
                # time_float takes time value and turns into a float: 1.192989
                continuous_time = time_float + time_offset
                # continuous_time takes time_offset from before and applies it: 11.192989

                clean_current = current_str.replace("NADC", "").lstrip("+-")
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
            time_offset = float(last_time_str)

    return all_readings
#
####################################################################################################
#
def merge_clean_data(cleaned_outputs):
    num_readings = len(cleaned_outputs[0])
    merged_data = []

    for i in range(num_readings):
        row = [str(i+1)]
        for keithley_output in cleaned_outputs:
            current, timestamp = keithley_output[i].split(',')
            row.append(current)
            row.append(timestamp)
        merged_data.append(row)

    return merged_data
#
####################################################################################################
#
async def sourceAndRead(allKeithleys, voltage, testTime):
    master_data = []
    tasks = []

    for index, keithley in enumerate(allKeithleys): # Allocates spaces for all data slots required per Keithley
        master_data.append(0)
        tasks.append(asyncio.create_task(keithleyTestThread(keithley, voltage, testTime, index+1)))
        
    graphtask = asyncio.create_task(graphThread(allKeithleys, voltage))

    # Awaits all tasks
    for index, task in enumerate(tasks):
        master_data[index] = await task
        
    graphtask.cancel()

    try:
        await graphtask
    except asyncio.CancelledError:
        print(f"Graph closed successfully")

    clean_data_list = []
    for index, individual_keithley_dataset in enumerate(master_data):
        clean_data_list.append(clean_data(individual_keithley_dataset))

    merged_data = merge_clean_data(clean_data_list)
    
    return merged_data
#
####################################################################################################
