####################################################################################################
#
# PNFLtest - 6/18/2025 - Tyler Frischknecht
# Pennathur Nanofluidics Lab Keithley Test Commands
#
####################################################################################################
# Import Libraries
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
def runTest(allGPIB, voltage, testTime, emails, name, info):
    testSuccess = False
    allKeithleys = []
    try:
        for GPIB in allGPIB:
            allKeithleys.append(connectToKeithley(GPIB))
        print("Setting limits.")
        setLimits(allKeithleys, voltage)
        print(f"Running test now! Check back in {testTime} minutes!")
        data = sourceAndRead(allKeithleys, voltage, testTime)
        testSuccess = True
    except pyvisa.VisaIOError as e:
        print(f"VisaIOError: {e}")
        print(f"Sorry about that, please run the test again!")
    except Exception as e:
        print(f"Exception: {e}")
        print(f"Sorry about that, please run the test again!")
    finally:
        for keithley in allKeithleys:
            try:
                keithley.close()
                print("Connection with Keithley terminated.")
            except Exception as e:
                print(f"Failed to close connection with Keithley - {e}")
    if testSuccess == True:
        # put data into file here!
        makeAllFiles(data, timestamp, len(allKeithleys))
        sendEmail(emails, timestamp, f"({voltage} V) "+ name, info)
#
####################################################################################################
# Connects to Keithley and returns keithley as object to write to with pyvisa
def connectToKeithley(GPIB):
    rm = pyvisa.ResourceManager()  # This will manage the connection
    keithley = rm.open_resource(f'GPIB::{GPIB}::INSTR')  # Open connection to the Keithley
    keithley.write("*CLS")
    keithley.write("*RST")
    print("Connected to Keithley Model:", keithley.query("*IDN?"))
    time.sleep(1)
    return(keithley)
#
####################################################################################################
#
def setLimits(allKeithleys, sourceVoltage):
    for keithley in allKeithleys:
        # Enable Voltage and Current Limit
        keithley.write("SOUR:VOLT:LIM:STAT 1")      # Turns voltage limiting on
        # Applies numerical limits
        keithley.write("SOUR:VOLT:LIM " + str(abs(sourceVoltage)+5))
        keithley.write("SENS:FUNC 'CURR:DC'")       # Sets the current measuring value to current
        keithley.write("SENS:CURR:RANG:AUTO 1")     # Enables auto range for current
        keithley.write("SENS:CURR:DIG 6")           # Sets float decimal digits to max (6)
        keithley.write("SYST:ZCH 1")                # Turns zero check on
        keithley.write("SYST:ZCH 0")                # Turns zero check off
        keithley.write("SYST:ZCOR 1")               # Turns zero correction on
#
####################################################################################################
#
def sourceAndRead(allKeithleys, voltage, testTime):
    data = []
    numReadings = 0
    nextReading = time.time()
    numKeithleys = len(allKeithleys)
 
    for keithley in allKeithleys:
        keithley.write("SOUR:VOLT " + str(voltage)) # Sets voltage output to voltage           
        keithley.write("OUTP 1")



    ##### MATPLOTLIB SETUP
    plot.ion() # Interactive Mode

    fig, allAxes = plot.subplots(numKeithleys + 1, 1, figsize=(10, 2 * (numKeithleys + 1)))
    fig.suptitle(f"Keithley Test Data at {voltage}V - {timestamp}")

    if numKeithleys == 1:
        allAxes = [allAxes[0], allAxes[1]]

    # NEW EPIC CONSOLIDATED DATA STORAGE for both individual and combined plots
    allxData = [] # Allocate X data for all Keithleys
    for _ in allKeithleys:    
        allxData.append([]) 

    allyData = [] # Allocate Y data for all Keithleys
    for _ in allKeithleys:   
        allyData.append([]) 

    individualPlotLines = []

    combinedPlotLines = [] # Lines for the combined plot

    # Set up individual plots (variable amount N individual plots above combined)
    for index, keithley in enumerate(allKeithleys):
        ax = allAxes[index] # Get the specific subplot for individual Keithley
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Current (A)")
        
        gpibAddress = None
        if "::" in keithley.resource_name:
            parts = keithley.resource_name.split("::") 
            gpibAddress = parts[1]
        else:
            gpibAddress = "N/A"

        ax.set_title(f"Keithley {index+1} (GPIB: {gpibAddress})")

        line, = ax.plot([], [], label=f'Keithley {index+1} (GPIB: {gpibAddress})')
        individualPlotLines.append(line) # Store lines for individual plots
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.2e}'))
        ax.grid(True)

    # Set up combined plot (always on bottom)
    combinedAxis = allAxes[numKeithleys] # The last subplot
    combinedAxis.set_xlabel("Time (s)")
    combinedAxis.set_ylabel("Current (A)")
    combinedAxis.set_title("All Keithleys")

    for index, keithley in enumerate(allKeithleys): # DOES NOT add new plots, adds lines to final subplot. Loop needed even though looks scary
        gpibAddress = None
        if "::" in keithley.resource_name:
            parts = keithley.resource_name.split("::") 
            gpibAddress = parts[1]
        else:
            gpibAddress = "N/A"
            
        line, = combinedAxis.plot([], [], label=f'Keithley {index+1} (GPIB: {gpibAddress})')
        combinedPlotLines.append(line) # Store lines for the combined plot

    combinedAxis.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.2e}'))
    combinedAxis.legend()
    combinedAxis.grid(True)

    fig.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title overlap

    warnings.filterwarnings("ignore", message=".*identical low and high.*")



    ### TEST LOOP
    while numReadings < int(testTime*120):
        nowTime = time.time()

        if (nowTime >= nextReading):
            allNewData = [numReadings]
            for index, keithley in enumerate(allKeithleys):
                keithley.write("INIT")
                newData = keithley.query("FETCH?")
                newData = newData.strip().split(',')
                newData[0] = newData[0][:-4] # Current
                newData[1] = float(newData[1][:-4]) # Time
                # newData[2] = int(newData[2][:-5])  # Reading number. Not needed!

                # Store data for this Keithley's individual plot
                allxData[index].append(newData[1])
                allyData[index].append(float(newData[0]))

                allNewData.extend(newData)
            data.append(allNewData)

            # Update stack of individual plots
            for index, line in enumerate(individualPlotLines):
                line.set_xdata(allxData[index]) 
                line.set_ydata(allyData[index]) 
                ax = allAxes[index] # Get the correct axis for limits
                if allxData[index] and allyData[index]: # Ensure data exists
                    ax.set_xlim(min(allxData[index]), max(allxData[index]))
                    q1, q3 = numpy.percentile(allyData[index], 25), numpy.percentile(allyData[index], 75)
                    iqr = q3 - q1
                    lowerBound = q1 - 2.5 * iqr
                    upperBound = q3 + 2.5 * iqr
                    ax.set_ylim(lowerBound, upperBound)
            
            # Update combined plot at bottom
            for index, line in enumerate(combinedPlotLines):
                line.set_xdata(allxData[index]) 
                line.set_ydata(allyData[index]) 

            # Calculate limits for the combined plot based on ALL consolidated data
            flatxDataCombined = [item for sublist in allxData for item in sublist] # Flatten allxData
            flatyDataCombined = [item for sublist in allyData for item in sublist] # Flatten allyData

            if flatxDataCombined and flatyDataCombined:
                combinedAxis.set_xlim(min(flatxDataCombined), max(flatxDataCombined))
                q1, q3 = numpy.percentile(flatyDataCombined, 25), numpy.percentile(flatyDataCombined, 75)
                iqr = q3 - q1
                lowerBound = q1 - 2.5 * iqr
                upperBound = q3 + 2.5 * iqr
                combinedAxis.set_ylim(lowerBound, upperBound)

            # Draw and flush events for the single figure
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            print(allNewData)
            numReadings += 1
            plot.pause(0.5)
            nextReading = nowTime + 0.5

    for keithley in allKeithleys:
        keithley.write("OUTP 0") # Turns voltage output off

    plot.ioff() # Disables interactive mode                                                    
    plot.savefig(imagePath) # Save the single combined figure to the original imagePath

    plot.close(fig)
  
    return(data)
#
####################################################################################################