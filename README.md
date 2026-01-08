# Kenya_Align.py

## Description

`Kenya_Align.py` was used for inter-sample GC-MS data alignment and compound classification in the publication Rebryk et al. 2024. Sci. Total Environ. https://doi.org/10.1016/j.scitotenv.2024.173183. 

## What does the script do

The script takes `Excel` file as input and does the following:
1.	Inter-sample alignment based on similarities in the compound names, CAS#, and integer retention times.
2.	Retrieval of InChIKey and SMILES values from the PubChem database (Kim et al. 2023. Nucleic Acids Res.) based on the compound names. 
3.	Classification of the compounds using ClassyFire Batch by Fiehn Lab (https://cfb.fiehnlab.ucdavis.edu/) based on the PubChem InChIKey values.

## Prerequisites

Before using the script, several applications/tools have to be installed:
1.	Python 3; https://www.python.org/downloads/windows/.
2.	All necessary modules (see **lines 35-48**).
3.	Google Chrome and ChromeDriver.

Modules can be intalled via Command Prompt as follows:
Type `cmd` in the Search line --> Click on the Command Prompt icon -->
--> Type: `pip install module_name` --> Press `Enter` --> Repeat for the next module.

Module names:
* tk
* pandas
* pubchempy
* selenium

## How to use the script

The script should be executed in Command Prompt.
To use the script, the following steps must be executed:
1.	Type `cmd` in the Search line --> Click on the Command Prompt icon --> Type: `python "the path to the script including the extension (.py)"`, e.g. `python "D:/Projects/Script S1.py"` --> Press `Enter`.
2.	Choose the files for processing in the new pop-up window and press `Open`. The processed file will be saved to the same location.

## Notes and recommendations

Before running the script, change the path to the working folder and the output file name (see **lines 243-248**).

This script is tailored to a certain data table format, i.e. the GCMSsolution (v4.52) software (Shimadzu, Japan) output file format.

The input file must contain at least the following columns to be processed: 
`"Substance"`, `"CAS"`, `"RT, min"`, and `"Area"`.

## License
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/mit)

Intended for academic and research use.
