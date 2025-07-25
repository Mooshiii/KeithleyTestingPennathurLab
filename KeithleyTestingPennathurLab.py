####################################################################################################
#
# Pennathur Laboratory Keithley 6517a Test Software
# Most Recent Rev: 7/24/2025
VERSION = "Main: 1.2.0"
#
####################################################################################################
# The good stuff starts here!
#
# Put email(s) you want data sent to here seperated by commas:
# Ex.          = "email@gmail.com, email2@gmail.com, email3@gmail.com"
EMAIL_ADDRESSES = "email@gmail.com, cooleremail@gmail.com"
#
# Put the title of your test here:
# Voltage is automatically added to the front! "Test1" -> "(5V) Test1"
# Ex.    = "100mM NaCl Test 1"
TEST_NAME = "Test Name Goes Here!"
#
# If you have any additional comments you would like to include, please include them here!
# Otherwise, you may leave the quotation marks blank:
# Ex.     = "We re-ran the test because the first chip was broken :("
TEST_NOTES = "Notes for your test can go here! They are sent to your email."
#
# Put the voltage you'd like to source here (in V):
# Ex.   = [5, 10, 20]
VOLTAGE = [0]
#
# Put the time you'd like the test to run here (in min):
# Ex.    = [10, 10, 300]
TEST_TIME = [0]
#
# Put the GPIB Addresses of the Keithleys you would like to test. (You can use up to 30!)
# Ex.           = [22, 24, 26]
GPIB_ADDRESSES = [0]
#
#
#
#
#
#
#
#
#
#
#
#
####################################################################################################
# Please don't touch this part unless you know what you're doing, its important!!
print("(Not an error): MAKE SURE YOU HAVE YOUR .env FILE CONFIGURED PROPERLY!")
from helper.pnfltest import runTest
if (len(VOLTAGE) != len(TEST_TIME)):
    print("Voltage list not same length as testTime list. Please ensure they both have the same number of items.")
    exit(1);

runTest(GPIB_ADDRESSES, VOLTAGE, TEST_TIME, EMAIL_ADDRESSES, TEST_NAME, TEST_NOTES, VERSION)
#
####################################################################################################
