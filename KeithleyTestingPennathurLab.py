####################################################################################################
#
# Pennathur Laboratory Keithley 6517a Test Software
# Most Recent Rev: 6/4/2025
#
####################################################################################################
# The good stuff starts here!
#
# Put email(s) you want data sent to here seperated by commas:
# Ex.          = "email@gmail.com, email2@gmail.com, email3@gmail.com"
emailAddresses = "default@default.com"
#
# Put the title of your test here:
# Voltage is automatically added to the front! "Test1" -> "(5V) Test1"
# Ex.    = "100mM NaCl Test 1"
testName = "Default Name!"
#
# If you have any additional comments you would like to include, please include them here!
# Otherwise, you may leave the quotation marks blank:
# Ex.     = "We re-ran the test because the first chip was broken :("
testNotes = "Default Phrase!"
#
# Put the voltage you'd like to source here (in V):
# Ex.   = [5, 10, 20]
voltage = [ ]
#
# Put the time you'd like the test to run here (in min):
# Ex.    = [10, 10, 300]
testTime = [ ]
#
# Put the GPIB Addresses of the Keithleys you would like to test. (You can use up to six!)
# Ex.           = [22, 24, 26]
AddressesOfGPIB = [ ]
####################################################################################################
# Please don't touch this part unless you know what you're doing, its important!!
from helper.pnfltest import runTest
if (len(voltage) != len(testTime)):
    print("Voltage list not same length as testTime list. Please ensure they both have the same amount of items.")
    exit(1);
for v, t in zip(voltage, testTime):
    print(f"--- Starting Test Cycle: Voltage: {v}, Time: {t} minutes ---")
    runTest(AddressesOfGPIB, v, t, emailAddresses, testName, testNotes)
    print(f"--- Finished Test Cycle: Voltage: {v}, Time: {t} minutes ---\n\n")
#
####################################################################################################