"""
A script used for inter-sample data alignment and classification.

Author: Andriy Rebryk, andrew.rebryk@gmail.com

To run the script, Python 3 (https://www.python.org/downloads/windows/),
all the necessary modules (see lines 35-48),
and Google Chrome have to be installed.

Modules can be intalled via Command Prompt as follows:
Type “cmd” in the Search line --> Click on the Command Prompt icon -->
--> Type: pip install module_name --> Press “Enter” --> Repeat for the next module.
Module names:
tk
pandas
pubchempy
selenium

Before running the script, change the path to the working folder and the output file name (see lines 243-248).

The script should be executed in Command Prompt.
For this, the following steps should be applied:

1. Type “cmd” in the Search line --> Click on the Command Prompt icon -->
--> Type: python "the path to the script including the extension (.py)", e.g. python "D:/Projects/Script S1.py" -->
--> Press “Enter”.

2. Navigate to the folder where the file to be processed is stored, select the file, and press “Open”.
The processed file will be saved to the same location.

This script is tailored to a certain data table format.
Feel free to change the script or use any part of it for your needs.
"""

#importing libraries/modules/functions
import tkinter as tk
import tkinter.filedialog
from tkinter.filedialog import askopenfilename
import time
import pandas as pd
from pandas import DataFrame
import pubchempy as pcp
from pubchempy import get_compounds, Compound
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

root = tk.Tk()
root.withdraw() #prevents the tkinter window to come up
#opening the file
xls_path = askopenfilename(title = 'Select Excel file for processing...')
root.destroy() #closing the window

#adding processing start time
startTime = time.strftime("%Y-%m-%d %H:%M:%S")
print(' ')
print('Processing start time:', startTime)
print(' ')

#storing the file as DataFrame (DF)
inXSL = pd.read_excel(xls_path, header = None, sheet_name = None)

#getting Excel sheet (sample) names; will be needed to add suffixes to column names for each sample
sheets = pd.ExcelFile(xls_path).sheet_names

#creating empty lists/arrays for further data appending
names = []
dflist = list()

#creating a list with columns to which sample name suffixes should NOT be added
#these are the columns that will be used as base for joining (merging) the samples
keep_same = {'Substance', 'CAS', 'RT_int'}

#creating separate DFs for each sample (sheet)
for i, sheet in enumerate(sheets):
    #storing each sheet separately as DF; DF name indexing starts from 1 not 0, i.e. from df1 to df18
    #deleting 4 top rows with sample information & the bottom row with concentration sums
    globals()['df' + str(i + 1)] = pd.read_excel(xls_path, header = None, sheet_name = sheet).iloc[4:-1]
    #deleting columns '#', 'm, ng toluene eqv', 'Relative %', and 'C, µg/m3 toluene eqv'
    #and setting the 5th row from the initial sheet ('Substance', 'CAS', 'RT, min', 'Area') as a header
    globals()['df' + str(i + 1)] = globals()['df' + str(i + 1)].drop(globals()['df' + str(i + 1)].columns[[0, 5, 6, 7]], axis = 1).rename(columns = globals()['df' + str(i + 1)].iloc[0]).iloc[1:].reset_index(drop = True)
    globals()['df' + str(i + 1)]['RT_int'] = pd.Series(dtype = 'float').fillna('') #creating empty column with RT integer values
    globals()['df' + str(i + 1)]['RT_int'] = globals()['df' + str(i + 1)]['RT, min'] #copying RT values to 'RT_int' column
    #rounding 'RT_int' column values for further alignment of 'Substance' duplicates
    globals()['df' + str(i + 1)]['RT_int'] = (pd.to_numeric(globals()['df' + str(i + 1)]['RT_int'], errors = 'coerce')).round(0).astype(int)
    #QC printing
    print('DF with RT_int:\n', globals()['df' + str(i + 1)])
    print(150*'*')
    names.append(str('df' + str(i + 1))) #appending DF names to an empty list
    #adding sample name suffixes to all columns except for 'Substance', 'CAS' & 'RT_int'
    globals()['df' + str(i + 1)].columns = ['{}{}'.format(c, '' if c in keep_same else str('_' + str(sheets[i]))) for c in globals()['df' + str(i + 1)].columns]
    #appending all DFs to an empty DF list
    dflist.append(globals()['df' + str(i + 1)])

#QC printing
print('DF names:\n', names)
print(150*'*')
print('All-DF list BEFORE:\n', dflist)
print(150*'*')

#joining all DFs (samples) based on similarities in 'Substance', 'CAS' & 'RT_int' columns
for df in dflist:
    df.index = pd.MultiIndex.from_arrays(df[['Substance', 'CAS', 'RT_int']].values.T) #setting 'Substance', 'CAS', and 'RT_int' column values as index values
    df = df.drop(df.columns[[0, 1, 4]], axis = 1, inplace = True) #dropping columns

#QC printing
print('DF list for joining:\n', dflist)
print(150*'*')

df_final = dflist[0].join(dflist[1:], how = 'outer') #joining all samples using outer join function
df_final = pd.DataFrame(df_final.reset_index()) #resetting index values to numerical ones
#renaming former index columns back to 'Substance', 'CAS', and 'RT_int, min'
df_final = df_final.rename(columns = {'level_0':'Substance'}).rename(columns = {'level_1':'CAS'}).rename(columns = {'level_2':'RT_int, min'})

#QC printing
print('With duplicates:\n', df_final)
print(150*'*')

#droping duplicate substances based on similarities in 'Substance' & 'RT_int, min' columns; keeping only first entry
df_final = df_final.drop_duplicates(subset = ['Substance', 'RT_int, min'], keep = 'first').reset_index(drop = True)
#QC printing
print('No duplicates:\n', df_final)
print(150*'*')

#re-sorting DF by 'RT_int, min' and 'Substance'
df_final = df_final.sort_values(by = ['RT_int, min', 'Substance'], ascending = True)
df_final = pd.DataFrame(df_final.reset_index(drop = True)) #resetting index values after re-sorting

#defyining the function to convert 'Substance' column values to InChIKey values
#InChIKeys are input for further batch classification at:
#https://cfb.fiehnlab.ucdavis.edu/
def Name_InChIKey_PubChem(IDs):
    try:
        results = pcp.get_compounds(IDs, 'name')
        for compound in results:
            return compound.inchikey
    except:
        return ''

#creating empty InChIKey column
df_final['InChIKey'] = pd.Series(dtype = 'float').fillna('')
#QC printing
print('df_final w/ empty column:\n', df_final)
print(150*'*')
indx = dict() #creating an empty dictionary to store DF indices for iteration

#searching for 'Substance' column entries using PubChem webpage
#and writing retrieved InChIKeys to an empty column
print('Retrieving InChIKeys from PubChem...')
print(' ')
for id in df_final['Substance']:
    indx[id] = df_final[df_final['Substance'] == id].index
    print(indx[id], '', id, '-->', Name_InChIKey_PubChem(id))
    df_final.loc[indx[id], 'InChIKey'] = Name_InChIKey_PubChem(id)

#QC printing
print(150*'*')
print('df_final w/ InChIKeys:\n', df_final)
print(150*'*')

#re-sorting table by 'InChIKey' column in descending fashion, N/As are moved to the bottom of the table
#this step is needed for further classificetion script to skip N/As
df_final = df_final.sort_values(by = 'InChIKey', ascending = False, na_position = 'last')
df_final = df_final.reset_index(drop = True)
#QC printing
print('Sorted df_final:\n', df_final)
print(150*'*')

#creating a list of InChIKeys
inchikeys = df_final['InChIKey']

print('Retrieving class data from ClassyFire...')
print(' ')

#launching Chrome browser
driver = webdriver.Chrome()
#navigating to the website
driver.get('https://cfb.fiehnlab.ucdavis.edu/')

try:
    #waiting for the search text area and the ClassyFy button;
    #the time can be adjusted based on page loading time
    search_textarea = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'inchikeys')))
    classify_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))

    #inserting InChIKeys from the list
    search_textarea.clear() #clearing the input field
    for key in df_final['InChIKey'].dropna().tolist(): #.dropna().tolist() is used to skip N/As, otherwise, the script crashes
        search_textarea.send_keys(key + "\n")

    #clicking the ClassyFy button after entering all InChIKeys
    classify_button.click()

    #waiting for the results to load; the time can be adjusted based on page loading time,
    #22000 sec are used to be sure the processing will be done before the script exits the webpage
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'results')))
    table = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'table')))
    reset_button = WebDriverWait(driver, 22000).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-warning')))

    #extracting data from the result table
    table_rows = table.find_elements(By.TAG_NAME, "tr") #finding all rows
    data = [] #creating an empty array to store the data
    for row in table_rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        cols = [col.text for col in cols]
        data.append(cols)
    print("*" * 150)

    #creating a list of column names; max. 11 columns are returned by ClassyFire
    column_names = ['InChIKey-2', 'Status', 'Kingdom', 'Superclass', 'Class', 'Subclass', 'Parent Level 1', 'Parent Level 2', 'Parent Level 3', 'Parent Level 4', 'Parent Level 5']
    #adjusting the data to align with the specified column names
    filled_data = [row + [None] * (len(column_names) - len(row)) for row in data]
    #converting the data to DF & adding specified column names
    df_classyfy = pd.DataFrame(filled_data, columns = column_names)
    #dropping the row where all values are None & resetting indices
    df_classyfy.dropna(how = 'all', inplace = True)
    df_classyfy.reset_index(drop = True, inplace = True)
    #QC printing
    print('ClassiFyed table:\n', df_classyfy)
    print("*" * 150)

finally:
    #closing the browser
    driver.quit()

#concatenating the ClassyFyed table and the initial table
out_DF = pd.concat([df_final, df_classyfy], axis = 1)
#dropping duplicate / unnecessary columns
out_DF = out_DF.drop(['InChIKey-2', 'Status'], axis = 1)
#copying data to output table & replacing possible N/A / NaN / None values with empty cells
out_DF = out_DF.fillna('')
#re-sorting the output table by 'RT_int, min' & 'Substance' columns  in ascending fashion
out_DF = out_DF.sort_values(by = ['RT_int, min', 'Substance'], ascending = True)
#resetting indices
out_DF = out_DF.reset_index(drop = True)
#QC printing
print('Out file:\n', out_DF)
print(150*'*')

#writing resulting DF to an Excel file
"""
Change the path according to your working folder path & output file name.
Do not change the file extension, i.e. .xlsx.
"""
out_DF.to_excel('D:/Projects/Aligned_&_ClassiFyed.xlsx', sheet_name = 'OUT', index = False)

print('Processing start time:', startTime)
print('Processing end time:', time.strftime("%Y-%m-%d %H:%M:%S"))
print(150*'*')
