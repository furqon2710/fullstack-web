import os
config_path = os.path.abspath(os.path.join(__file__,"../.."))

import sys
sys.path.append(config_path)

import config as CFG

crontab_folder_path = os.path.abspath(os.path.join(__file__,"../")) + "/"

venv_python_path = CFG.VENV_FOLDER_PATH + "bin/python"

if CFG.IS_USE_VENV == "YES":
    EXECUTOR = venv_python_path
else:
    EXECUTOR = "python3"


list_crontab = [
    ["* * * * *", "update_transaksi.py"]
]

#Check if file exist
is_error = 0
for x in list_crontab:
    full_path = crontab_folder_path+x[1]
    if os.path.exists(full_path) == False:
        print("ERROR!!! : "+ x[1] + " is not exist")
        is_error = 1

if is_error == 1:
    sys.exit("\nFailed to generate crontab list. \nMake sure all python file is exist")
else:
    for x in list_crontab:
        full_crontab_path = x[0] + " " +EXECUTOR+ " " + crontab_folder_path + x[1]
        print(full_crontab_path)