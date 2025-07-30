####################################################################################################
#
# PNFLmail - 7/29/2025 - Tyler Frischknecht
# Pennathur Nanofluidics Lab Email
MAIL_VERSION = "   Mail: 1.2.1"
#
####################################################################################################
# Import Libraries
import smtplib      # Used to send SMTP emails
import ssl          # Used for ssl and tls protocols
import os           # Allows file creation and manipulation
import datetime     # Allows calender style timestamp retrieval for final email
from email import encoders                          # Helps encode attachments for email (base64)
from email.mime.base import MIMEBase                # Creates base email attachments
from email.mime.multipart import MIMEMultipart      # Handles emails with multiple parts, i.e. subject, text, attachments
from email.mime.text import MIMEText                # Creates plain text email content from string literals
from dotenv import load_dotenv
load_dotenv()
#
####################################################################################################
# Important Global Variables
smtpPort = 587                  # Standard secure SMTP port
smtpServer = "smtp.gmail.com"   # Google SMTP
smtpUsername = os.getenv("SMTP_USERNAME")  # Email Username        
smtpPassword = os.getenv("SMTP_PASSWORD") # pip install python-dotenv
#
####################################################################################################
# Main email function
def sendEmail(userEmailsList, timestamp, testName = "Your Test", testAdditionalInfo = "The data is attached to the email!", GRAPH = True, version="UNK"):
    version += MAIL_VERSION
    allFiles = []
    if __name__ == "__main__":
        allFiles.append(os.path.join('..', 'data', f"data{timestamp}.csv"))
        allFiles.append(os.path.join('..', 'data', f"data{timestamp}.xlsx"))
        if GRAPH:
            allFiles.append(os.path.join('...', 'data', f"data{timestamp}.png"))
    else:
        allFiles.append(os.path.join('helper', 'data', f"data{timestamp}.csv"))
        allFiles.append(os.path.join('helper', 'data', f"data{timestamp}.xlsx"))
        if GRAPH:
            allFiles.append(os.path.join('helper', 'data', f"data{timestamp}.png"))

    if type(userEmailsList) != list:
        userEmailsList = userEmailsList.split(", ") # Separating string into list of separate emails.
    if "keithley.test.data.results@gmail.com" not in userEmailsList:
        userEmailsList.append("keithley.test.data.results@gmail.com")

    # TEXT FORMATTING
    message = MIMEMultipart() # Setting up the multi part message
    message['From'] = smtpUsername
    message['Subject'] = f"{testName}  -  {timestamp}"

    messageBody = "\n".join([
        f"Your test is complete!",
        f"{testName}  -  {timestamp}",
        f"",
        f"Your notes: {testAdditionalInfo}",
        f"",
        f"VERSIONS:   {version}",
        f"If you encountered any issues, please send an email to tfrischknecht@ucsb.edu or tbrooksdf@gmail.com",
        f"Good luck and happy testing!"]) # Full message contents
       
    message.attach(MIMEText(messageBody, 'plain')) # Attach messageBody above as plain text.

    # ATTACHMENTS
    for filePath in allFiles:
        with open(filePath, 'rb') as file: # Open the file as raw binary
            attachment = MIMEBase('application', 'octet-stream') # Arguments 'application' and 'octet-steam' tells MIME to treat it as RB
            attachment.set_payload(file.read()) # Attaches files as RB of data of files
            encoders.encode_base64(attachment) # Encodes the files RB values into base64 for email
            attachment.add_header('Content-Disposition', f"attachment; filename={os.path.basename(filePath)}")
            message.attach(attachment) # attaches attachment

    # SENDING EMAIL
    error = True
    emailContext = ssl.create_default_context() # Establsh context for email

    try:
        server = smtplib.SMTP(smtpServer, smtpPort)
        server.starttls(context=emailContext)
        server.login(smtpUsername, smtpPassword)
        for email in userEmailsList:
            try:
                print(f"Sending email to: {email}...   ", end="")
                if 'To' in message:
                    del message['To']
                message['To'] = email
                server.sendmail(smtpUsername, message['To'], message.as_string())
                print("email sent successfully!")
            except:
                print(f"email to {email} unsuccessful :(")
    except Exception as error:
        print(error)
    finally:
        server.quit()
#
####################################################################################################
