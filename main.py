from get_px_power.get_px_power import get_px_power
from cal_px_power.cal_px_power import cal_px_power
import argparse
import textwrap
import time
import sys

parser = argparse.ArgumnetParser(description="Script to do PX power extraction and calculation", usage="Run python3 main.py -h for more info", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-p", "--preset", type=int, required=True, help=textwrap.dedent('''Inform if preset inputs should be used,
Type = int'''))
parser.add_argument("-s", "--selection", type=int, required=True, help=textwrap.dedent('''Selection choice for script to be executed
1 - Get_PX_Power.py
2 - Cal_PX_Power.py
3 - Get_PX_Power.py + Cal_PX_Power.py
Type = int'''))
parser.add_argument("-d", "--dir_key", type=str, help=textwrap.dedent('''Keyword to determine directories to process,
Default = POSTSI_SUSPEND'''))
parser.add_argument("-f", "--file_name", type=str, help=textwrap.dedent('''File name for script to use for input/output,
Default = Power'''))
parser.add_argument("-l", "--lcpu_num", type=int, help=textwrap.dedent('''Number of LCPU cores in design,
Default = 6'''))
parser.add_argument("-m", "--mcpu_num", type=int, help=textwrap.dedent('''Number of MCPU cores in design,
Default = 0'''))
parser.add_argument("-b", "--bcpu_num", type=int, help=textwrap.dedent('''Number of BCPU cores in design,
Default = 2'''))

args = parser.parse_args()

script_run_selection = args.selection
preset_input         = args.preset

if int(script_run_selection) == 1 or int(script_run_selection) == 2 or int(script_run_selection) == 3:
    print("Script run selection is valid")
    if preset_input:
        directory_keyword = "POSTSI_SUSPEND"
        file_name         = "Power"
        lcpu_num          = 6
        mcpu_num          = 0
        bcpu_num          = 2
    else:
        if int(script_run_selection) == 1 or int(script_run_selection) == 3:
            directory_keyword = args.dir_key
            file_name         = args.file_name
            lcpu_num          = args.lcpu_num
            mcpu_num          = args.mcpu_num
            bcpu_num          = args.bcpu_num
        elif int(script_run_selection) == 2:
            file_name = args.file_name
    
    ## Set core_num variables to default values if user left empty
    if int(script_run_selection) == 1 or int(script_run_selection) == 3:
        if not(lcpu_num and str(lcpu_num).split):
            lcpu_num = 6
        if not(mcpu_num and str(mcpu_num).split):
            mcpu_num = 0
        if not(bcpu_num and str(bcpu_num).split):
            bcpu_num = 2
    
    ## Set file_name variable to default value if user left empty
    if not(file_name and file_name.split):
        get_output_file_name = "Power.xlsx"
    else:
        get_output_file_name = file_name + ".xlsx"

    cal_output_file_name = get_output_file_name.split(".")[0] + "_select.xlsx"

    start_time  = time.time()
    offset_time = 0

    if int(script_run_selection) == 1:
        ## Source Get_PX_Power.py script
        get_px_power(directory_keyword, get_output_file_name, lcpu_num, mcpu_num, bcpu_num)
    elif int(script_run_selection) == 2:
        ## Source Cal_PX_Power.py script
        offset_time = cal_px_power(get_output_file_name, cal_output_file_name)
    elif int(script_run_selection) == 3:
        ## Source both Get_PX_Power.py and Cal_PX_Power.py scripts
        get_px_power(directory_keyword, get_output_file_name, lcpu_num, mcpu_num, bcpu_num)
        offset_time = cal_px_power(get_output_file_name, cal_output_file_name)

    # Runtime calculation
    end_time     = time.time()
    duration_sec = end_time - start_time - offset_time

    if duration_sec//60 != 0:
        duration_min = duration_sec/60
        if duration_min//60 != 0:
            duration = duration_min/60
            tag      = "hr"
        else:
            duration = duration_min
            tag      = "min"
    else:
        duration = duration_sec
        tag      = "sec"

    print("")
    print("")
    print("All power scripts finished")
    print("Process took ", duration, tag, "to finish")
    print("Please check output details in Excel file(s)")
else:
    print("")
    print("")
    print("Selection choice of  ", script_run_selection, "is invalid")
    print("Please check and rerun main.py again")
    sys.exit(1)