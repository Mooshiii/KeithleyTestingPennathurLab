####################################################################################################
#
# PNFLfile - 6/17/2025 - Tyler Frischknecht
# Pennathur Nanofluidics Lab File Storage
VERSION = "   File: 1.2.0"
#
####################################################################################################
# Import Libraries
import os           # Allows file creation and manipulation
import numpy        # Allows advanced array math
import pandas       # Allows excel spreadsheet and csv creation
#                   # For excel to work, run "pip install openpyxl"
#
####################################################################################################
# Formatting list from strings returned by Keithley. (DEFUNCT)
# def formatData(startData):
#     print("-"*100)
#     print("Processing Data:")
#     formattedData = [["Reading Number", "Time", "Current"]]
#     compareData = startData[0][0].strip().split(',')
#     compareData[0] = compareData[0][:-4]
#    compareData[1] = float(compareData[1][:-4])
#    compareData[2] = int(compareData[2][:-5])
#    formattedData.append([0, 0.05, compareData[0]])
#    for line in startData[1:]:
#        workingLine = line[0].strip().split(',')
#        workingLine[0] = workingLine[0][:-4]
#        workingLine[1] = float(workingLine[1][:-4]) - compareData[1]
#        workingLine[2] = int(workingLine[2][:-5]) - compareData[2]
#        formattedData.append([workingLine[2], workingLine[1], workingLine[0]])
#        print(f"Reading #{workingLine[2]:.0f}:\t{workingLine[1]:.6f} secs\t{workingLine[0]} A")
#    print("Data Processed!")
#    print("-"*100)
#    return(formattedData)
#
####################################################################################################
# Making all files from list.
def makeAllFiles(data, timestamp, numKeithleys):
    if __name__ == "__main__":
        csvPath = os.path.join('..', 'data', f"data{timestamp}.csv")
        xlsxPath = os.path.join('..', 'data', f'data{timestamp}.xlsx')
    else:
        csvPath = os.path.join('helper', 'data', f'data{timestamp}.csv')
        xlsxPath = os.path.join('helper', 'data', f'data{timestamp}.xlsx')

    insertHeader = ["Reading #"]
    for _ in range(0, numKeithleys):
        insertHeader.append("Current")
        insertHeader.append("Time")
    formattedData = data
    formattedData.insert(0, insertHeader)

    print("Creating CSV and XSLX files.")
    df = pandas.DataFrame(formattedData[1:], columns = formattedData[0])
    df.to_csv(csvPath, index=False)
    print("CSV Made!")
    df.to_excel(xlsxPath, index=False)
    print("XLSX Made!")

    return VERSION
#
####################################################################################################
#
if __name__ == "__main__":
    fakeData = [["Header1", "Header2", "Header3"],[1,2,3],[4,5,6],[7,8,9]]
    makeAllFiles(fakeData, "timestamp", 1)
#
####################################################################################################
