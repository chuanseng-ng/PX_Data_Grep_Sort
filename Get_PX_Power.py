from distutils.command.clean import clean
from os import listdir, stat, remove
from os.path import isfile, join
from tqdm import tqdm
from glob import glob
import pandas as pd
import numpy as np
import xlsxwriter
import time
import sys
import re


# Ask user to provide keyword to calculate power for
directory_keyword = input("Enter keyword for directory: ")
print("")
# Ask user for output file name, else will default to Power.xlsx
print("Default output file name is Power.xlsx")
output_file_name = input("Enter output file name: ")
print("")

if not(output_file_name and output_file_name.split):
    output_file_name = "Power.xlsx"

# Ask user for core breadown
print("Please provide the core number breakdown for project")
print("If left empty, default will be set: LCPU = 4, MCPU = 0, BCPU = 0")
lcpu_number = input("Enter number of LCPU cores: ")
mcpu_number = input("Enter number of MCPU cores: ")
bcpu_number = input("Enter number of BCPU cores: ")
print("")

if not(lcpu_number and lcpu_number.split):
    lcpu_number = 4
if not(mcpu_number and mcpu_number.split):
    mcpu_number = 0
if not(bcpu_number and bcpu_number.split):
    bcpu_number = 0

start_time = time.time()


# Class initialization
## Hierarchy + Type datasheet class
class HierarchyTypeDatasheet(object):
    def __init__(self, data_list = None, power_rail_dict = None, run_name_count = None, run_name_dict = None):
        self.data_list           = data_list
        self.power_rail_dict     = power_rail_dict
        self.run_name_count      = run_name_count
        self.run_name_dict       = run_name_dict
        self.power_rail_position = 1


# Function initialization
## Grep leakage line details
def grep_leakage(keyword_file, write_file, temperature_list):
    search_term     = "Cell Leakage Power"
    open_file_read  = open(keyword_file, "r")
    open_file_write = open(write_file, "w")

    if any(check in keyword_file for check in temperature_list):
        for line in tqdm(open_file_read, desc = "Grep leakage keyword in file"):
            if re.search(search_term, line):
                temp_input = keyword_file + " , " + line
                open_file_write.write(temp_input)

    open_file_write.close()

## Grep internal & switching line details
def grep_dynamic(keyword_file, write_file, temperature_list):
    search_internal_term  = "Cell Internal Power"
    search_switching_term = "Net Switching Power"
    open_file_read        = open(keyword_file, "r")
    open_file_write       = open(write_file, "w")
    temp_input            = keyword_file

    if not(any(check in keyword_file for check in temperature_list)):
        for line in tqdm(open_file_read, desc = "Grep internal keyword in file"):
            if re.search(search_switching_term, line):
                sub_input    = re.sub('\(.+\)', '', line)
                edited_input = sub_input.strip()
                temp_input   = temp_input + " , " + edited_input
            elif re.search(search_internal_term, line):
                temp_input = temp_input + " , " + line
        open_file_write.write(temp_input)
    
    open_file_write.close()

## Extract power rail details
def power_rail_search(rpt_name):
    search_result = re.search('UPF_(.+?)_rail', rpt_name).group(1)

    return search_result

## Split dynamic & leakage files
def leakage_dynamic_sort(rpt_name):
    if re.search('pwr(.+?).rpt', rpt_name) != None:
        search_result = re.search('pwr(.+?).rpt', rpt_name).group(1)
        temperature   = search_result.split("_")[4]
        sort_type     = "leakage"
    else:
        temperature = ""
        sort_type   = "dynamic"

    return temperature, sort_type

## Search for lowest hierarchy name in report name
def hierarchy_name_search(dataframe_dict, rpt_name, hierarchy_2d_list, cell_levels):
    for hierarchy_list in tqdm(hierarchy_2d_list, desc = "Go through lists within 2D list of lists for hierarchy names"):
        if any(hierarchy in rpt_name for hierarchy in hierarchy_list):
            general_hierarchy_name = hierarchy_list[0]
        
    for cell_level in cell_levels:
        if cell_level in rpt_name:
            rpt_extracted_cell_level = cell_level

    extracted_core_num = rpt_extracted_cell_level.split("_")[1]

    if general_hierarchy_name is "TOP":
        dict_checker                  = general_hierarchy_name
        checked_leakage_datalist_name = general_hierarchy_name.lower() + "_leakage_datalist"
        checked_dynamic_datalist_name = general_hierarchy_name.lower() + "_dynamic_datalist"
    else:
        dict_checker                  = general_hierarchy_name + extracted_core_num
        checked_leakage_datalist_name = general_hierarchy_name.lower() + "_" + extracted_core_num + "_leakage_datalist"
        checked_dynamic_datalist_name = general_hierarchy_name.lower() + "_" + extracted_core_num + "_dynamic_datalist"

    if dict_checker not in dataframe_dict:
        dataframe_dict[dict_checker] = {"leakage_list": checked_leakage_datalist_name, "dynamic_list": checked_dynamic_datalist_name}

    return dataframe_dict, general_hierarchy_name, rpt_extracted_cell_level

## Generate top header class object
def create_top_header(hierarchy_name):
    top_header_list         = ["TOP"]
    temperature_header_list = ["Temperature"]
    power_rail_dict         = {}
    run_name_count          = 1
    run_name_dict           = {}

    top_list = []
    top_list.append(top_header_list)
    top_list.append(temperature_header_list)

    new_top_datasheet = HierarchyTypeDatasheet(top_list, power_rail_dict, run_name_count, run_name_dict)

    return new_top_datasheet

## Generate core header class object
def create_core_header(hierarchy_name, cell_level):
    core_header             = hierarchy_name
    updated_core_header      = core_header + "_" + cell_level.split("_")[1]
    temperature_header_list = ["Temperature"]
    power_rail_dict         = {}
    run_name_count          = 1
    run_name_dict           = {}

    updated_core_header_list = []
    updated_core_header_list.append(updated_core_header)

    core_list = []
    core_list.append(updated_core_header_list)
    core_list.append(temperature_header_list)

    new_core_datasheet = HierarchyTypeDatasheet(core_list, power_rail_dict, run_name_count, run_name_dict)

    return new_core_datasheet

## Generate LCPU header class object
def create_lcpu_header(hierarchy_name, cell_level):
    lcpu_header             = "LCPU"
    updated_lcpu_header      = lcpu_header + "_" + cell_level.split("_")[1]
    temperature_header_list = ["Temperature"]
    power_rail_dict         = {}
    run_name_count          = 1
    run_name_dict           = {}

    updated_lcpu_header_list = []
    updated_lcpu_header_list.append(updated_lcpu_header)

    lcpu_list = []
    lcpu_list.append(updated_lcpu_header_list)
    lcpu_list.append(temperature_header_list)

    new_lcpu_datasheet = HierarchyTypeDatasheet(lcpu_list, power_rail_dict, run_name_count, run_name_dict)

    return new_lcpu_datasheet

## Generate MCPU header class object
def create_mcpu_header(hierarchy_name, cell_level):
    mcpu_header             = "mcpu"
    updated_mcpu_header      = mcpu_header + "_" + cell_level.split("_")[1]
    temperature_header_list = ["Temperature"]
    power_rail_dict         = {}
    run_name_count          = 1
    run_name_dict           = {}

    updated_mcpu_header_list = []
    updated_mcpu_header_list.append(updated_mcpu_header)

    mcpu_list = []
    mcpu_list.append(updated_mcpu_header_list)
    mcpu_list.append(temperature_header_list)

    new_mcpu_datasheet = HierarchyTypeDatasheet(mcpu_list, power_rail_dict, run_name_count, run_name_dict)

    return new_mcpu_datasheet

## Generate BCPU header class object
def create_bcpu_header(hierarchy_name, cell_level):
    bcpu_header             = "bcpu"
    updated_bcpu_header      = bcpu_header + "_" + cell_level.split("_")[1]
    temperature_header_list = ["Temperature"]
    power_rail_dict         = {}
    run_name_count          = 1
    run_name_dict           = {}

    updated_bcpu_header_list = []
    updated_bcpu_header_list.append(updated_bcpu_header)

    bcpu_list = []
    bcpu_list.append(updated_bcpu_header_list)
    bcpu_list.append(temperature_header_list)

    new_bcpu_datasheet = HierarchyTypeDatasheet(bcpu_list, power_rail_dict, run_name_count, run_name_dict)

    return new_bcpu_datasheet

## Dump leakage/dynamic power data into correct positions in data_list
def data_dumping(datalist, power_rail, run_name, temperature, temperature_buffer, leakage_power, switching_power, internal_power):
    for key, value in datalist.power_rail_dict.items():
        if value == power_rail:
            if temperature != 0:
                temp_rail_position = int(key)
            else:
                temp_x_position = int(key)

    if temperature != 0:
        for count in (range(temp_rail_position, temp_rail_position + temperature_buffer)):
            if datalist.data_list[1][count] == temperature:
                temp_x_position = count
    
    for key, value in datalist.run_name_dict.items():
        if value == run_name:
            temp_y_position = int(key) + 1

    if temperature == 0:
        remainder_power = float(switching_power) + float(internal_power)
        datalist.data_list[temp_y_position][temp_x_position] = float(remainder_power)
    else:
        datalist.data_list[temp_y_position][temp_x_position] = float(leakage_power)

    return datalist

## Initialize all relevant leakage/dynamic data into corresponding data_list positions
def init_data_dump(datalist, power_rail, run_name, temperature, temperature_list, temperature_buffer, leakage_power, switching_power, internal_power):
    if run_name not in datalist.run_name_dict.values():
        run_name_list = []
        run_name_list.append(run_name)

        datalist.data_list.append(run_name_list)
        datalist.run_name_dict[datalist.run_name_count] = run_name
        datalist.run_name_count = str(int(datalist.run_name_count) + 1)

        if power_rail in datalist.power_rail_dict.values():
            for _ in tqdm(range(int(list(datalist.power_rail_dict.keys())[-1]) + 5), desc = "Filling empty buffer in new urn name row after power rail filled"):
                datalist.data_list[int(datalist.run_name_count)].append("")
        
    if power_rail not in datalist.power_rail_dict.values():
        datalist.data_list[0].append(power_rail)
        datalist.power_rail_dict[datalist.power_rail_position] = power_rail

        if temperature != 0:
            datalist.power_rail_position = str(int(datalist.power_rail_position) + int(temperature_buffer))

            for _ in tqdm(range(1, temperature_buffer), desc = "Filling empty buffer in power rail row"):
                datalist.data_list[0].append("")

            if len(datalist.data_list[int(datalist.run_name_count)]) == len(datalist.data_list[0]) - 5:
                for _ in tqdm(range(temperature_buffer), desc = "Filling empty buffer in run name row"):
                    datalist.data_list[int(datalist.run_name_count)].append("")
            else:
                for _ in tqdm(range(int(list(datalist.power_rail_dict.keys())[-1]) + 5), desc = "Filling empty buffer in new run name row after addition of new power rail"):
                    datalist.data_list[int(datalist.run_name_count)].append("")

            datalist.data_list[1].extend(temperature_list)
        else:
            datalist.power_rail_position = str(int(datalist.power_rail_position) + 1)

            if len(datalist.data_list[int(datalist.run_name_count)]) == len(datalist.data_list[0]) - 1:
                datalist.data_list[int(datalist.run_name_count)].append("")
            else:
                for _ in tqdm(range(int(list(datalist.power_rail_dict.keys())[-1]) + 1), desc = "Filling empty buffer in new run name row after addition of new power rail"):
                    datalist.data_list[int(datalist.run_name_count)].append("")

    if temperature != 0:
        updated_datalist = data_dumping(datalist, power_rail, run_name, temperature, temperature_buffer, leakage_power, 0, 0)
    else:
        updated_datalist = data_dumping(datalist, power_rail, run_name, 0, 0, 0, switching_power, internal_power)

    return updated_datalist

## Check if user provided core number is valid
def cpu_num_checker(cpu_number, cpu_type, dataframe_dict):
    if int(cpu_number) != 0:
        if any(cpu_type in key for key in dataframe_dict.keys()):
            alt_cpu_number = int(cpu_number) - 1
        else:
            cpu_number     = 0
            alt_cpu_number = 0
    else:
        alt_cpu_number = 0

    return cpu_number, alt_cpu_number

## Remove row index and column header in top dataframe
def top_dataframe_cleanup(dataframe):
    dataframe_iloc         = dataframe
    dataframe_iloc.columns = pd.RangeIndex(dataframe_iloc.columns.size)
    dataframe_column_num   = len(dataframe.columns)
    add_count              = 0

    if any(item is None for item in dataframe.iloc[0, :]):
        for count in range(dataframe_column_num - 1):
            while count + add_count < dataframe_column_num and dataframe.iloc[0, count] is None:
                add_count += 1
                dataframe_iloc.drop(columns = dataframe_iloc.columns[count], inplace = True)
            if count + add_count == dataframe_column_num - 1:
                break
    else:
        dataframe_iloc = dataframe

    dataframe_iloc.reset_index(inplace=True, drop=True)

    if "Temperature" in dataframe_iloc[0][1]:
        temp_dataframe = dataframe_iloc.drop([0, 1], axis = 0)
    else:
        temp_dataframe = dataframe_iloc.drop([0], axis = 0)

    clean_dataframe = temp_dataframe.drop(columns = 0)

    return clean_dataframe

## Remove row index and column header in cpu dataframe
def cpu_dataframe_cleanup(dataframe):
    dataframe_iloc         = dataframe
    dataframe_iloc.columns = pd.RangeIndex(dataframe_iloc.columns.size)
    dataframe_column_num   = len(dataframe.columns)
    add_count              = 0

    if any(item is None for item in dataframe.iloc[0, :]):
        for count in range(dataframe_column_num - 1):
            while count + add_count < dataframe_column_num and dataframe.iloc[0, count] is None:
                add_count += 1
                dataframe_iloc.drop(columns = dataframe_iloc.columns[count], inplace = True)
            if count + add_count == dataframe_column_num - 1:
                break
    else:
        dataframe_iloc = dataframe

    dataframe_iloc.reset_index(inplace=True, drop=True)

    if "Temperature" in dataframe_iloc[0][1]:
        temp_dataframe = dataframe_iloc.drop([0, 1], axis = 0)
    else:
        temp_dataframe = dataframe_iloc.drop([0], axis = 0)
    
    clean_dataframe = temp_dataframe.drop(columns = 0)

    return clean_dataframe

## Perform arthimetic operations on top dataframe to generate top_only dataframe
def top_only_df_calculation(cpu_number, alt_cpu_number, core_num_checker, cpu_type, dataframe_dict):
    alt_core_num_checker = int(core_num_checker) + 1

    if int(cpu_number) != 0:
        for key in dataframe_dict.keys():
            if cpu_type in key:
                dataframe_dict[key]["clean_leakage_df"] = cpu_dataframe_cleanup(dataframe_dict[key]["leakage_df"])
                dataframe_dict[key]["clean_dynamic_df"] = cpu_dataframe_cleanup(dataframe_dict[key]["dynamic_df"])

                if str(core_num_checker) in key:
                    main_key = key
                elif cpu_type in key and str(alt_core_num_checker) in key:
                    sub_key  = key

    if "Temp" not in dataframe_dict.keys():
        dataframe_dict["Temp"]               = {}
        dataframe_dict["Temp"]["leakage_df"] = dataframe_dict["TOP"]["clean_leakage_df"] - dataframe_dict[main_key]["clean_leakage_df"] - int(alt_cpu_number)*dataframe_dict[sub_key]["clean_leakage_df"]
        dataframe_dict["Temp"]["dynamic_df"] = dataframe_dict["TOP"]["clean_dynamic_df"] - dataframe_dict[main_key]["clean_dynamic_df"] - int(alt_cpu_number)*dataframe_dict[sub_key]["clean_dynamic_df"]
    else:
        dataframe_dict["Temp"]["leakage_df"] = dataframe_dict["Temp"]["leakage_df"] - dataframe_dict[main_key]["clean_leakage_df"] - int(alt_cpu_number)*dataframe_dict[sub_key]["clean_leakage_df"]
        dataframe_dict["Temp"]["dynamic_df"] = dataframe_dict["Temp"]["dynamic_df"] - dataframe_dict[main_key]["clean_dynamic_df"] - int(alt_cpu_number)*dataframe_dict[sub_key]["clean_dynamic_df"]

    return dataframe_dict

## Populate row index and column header to top_only dataframe
def add_row_col_dataframe(dataframe_dict):
    top_column_only_leakage_series = (dataframe_dict["TOP"]["leakage_df"].drop([0, 1], axis = 0)).iloc[:, 0]
    top_column_only_dynamic_series = (dataframe_dict["TOP"]["dynamic_df"].drop([0, 1], axis = 0)).iloc[:, 0]

    top_column_only_leakage_dataframe    = top_column_only_leakage_series.to_frame()
    top_column_only_dynamic_dataframe    = top_column_only_dynamic_series.to_frame()
    top_no_header_only_leakage_dataframe = top_column_only_leakage_dataframe.join(dataframe_dict["Temp"]["leakage_df"])
    top_no_header_only_dynamic_dataframe = top_column_only_dynamic_dataframe.join(dataframe_dict["Temp"]["dynamic_df"])

    top_row_only_leakage_dataframe_trans = dataframe_dict["TOP"]["leakage_df"].T
    top_row_only_dynamic_dataframe_trans = dataframe_dict["TOP"]["dynamic_df"].T
    top_row_only_leakage_dataframe_trans.drop(top_row_only_leakage_dataframe_trans.iloc[:, 2:-1], inplace=True, axis=1)
    top_row_only_dynamic_dataframe_trans.drop(top_row_only_dynamic_dataframe_trans.iloc[:, 2:-1], inplace=True, axis=1)
    top_row_only_leakage_dataframe_trans_iloc = top_row_only_leakage_dataframe_trans.iloc[:, :-1]
    top_row_only_dynamic_dataframe_trans_iloc = top_row_only_dynamic_dataframe_trans.iloc[:, :-1]

    top_no_header_only_leakage_dataframe_trans = top_no_header_only_leakage_dataframe.T
    top_no_header_only_dynamic_dataframe_trans = top_no_header_only_dynamic_dataframe.T
    top_only_leakage_dataframe_trans           = pd.concat([top_row_only_leakage_dataframe_trans_iloc, top_no_header_only_leakage_dataframe_trans], axis=1)
    top_only_dynamic_dataframe_trans           = pd.concat([top_row_only_dynamic_dataframe_trans_iloc, top_no_header_only_dynamic_dataframe_trans], axis=1)
    dataframe_dict["TOP_only"]["leakage_df"]   = top_only_leakage_dataframe_trans.T
    dataframe_dict["TOP_only"]["dynamic_df"]   = top_only_dynamic_dataframe_trans.T

    dataframe_dict["TOP_only"]["leakage_df"][0][0] = 'TOP_only'
    dataframe_dict["TOP_only"]["dynamic_df"][0][0] = 'TOP_only'

    return dataframe_dict

# First part -> Grep leakage details from all files
keyword_directory_path = "../all_out/*" + directory_keyword + "*"
keyword_directories    = glob(keyword_directory_path)

cell_levels       = ["mcusys_par_wrap", "core_0", "core_1", "core_2", "core_3", "core_4", "core_5", "core_6", "core_7"]
hierarchy_2d_list = [["TOP", "mcusys_par_wrap"],
                     ["LCPU", "ananke_core", "hayes_core", "hunter_core"],
                     ["BCPU", "enyo_core", "hercules_core", "matterhorn_core"]]
temperature_list  = ["25c", "45c", "65c", "85c", "105c"]
dataframe_dict    = {}

current_path = "./"

existing_temp_files = [f for f in listdir(current_path) if isfile(join(current_path, f))]

## Remove existing temp_* files to avoid overlaps/conflicts
for temp_file in tqdm(existing_temp_files, desc = "Removing existing temp_* files"):
    if "txt" in temp_file:
        remove(temp_file)

if len(keyword_directories) == 0:
    print("Keyword not present in ../all_out path!!!")
    print("Please check the current ../all_out path for a valid keyword!!!")
    sys.exit(1)

for directory in tqdm(keyword_directories, desc = "Keyword directory UPF_DVDD files breakdown"):
    keyword_file_path = directory + "/report/*/active/UPF_DVDD*.rpt"
    upf_dvdd_files    = glob(keyword_file_path)
    write_file        = "temp_" + directory.split("/")[2] + ".txt"

    temp_clean_file = open(write_file, "w")
    temp_clean_file.write("")
    temp_clean_file.close()

    for keyword_file in tqdm(upf_dvdd_files, desc = "Keyword UPF_DVDD files breakdown"):
        for level in tqdm(cell_levels, desc = "Check for correct cell levels in files"):
            if level in keyword_file:
                grep_leakage(keyword_file, write_file, temperature_list)
                grep_dynamic(keyword_file, write_file, temperature_list)

    # Remove empty files
    if stat(write_file).st_size == 0:
        remove(write_file)


# Second part -> Sorting details into list-of-list table/dataframe
current_temp_files = [f for f in listdir(current_path) if isfile(join(current_path, f))]

temperature_header_list = ["Temperature"]
temperature_buffer      = 5
power_rail_position     = 1
power_rail_dict         = {}
run_number              = 1
run_name_dict           = {}
used_header_list        = ["TOP"]
hierarchy_dict          = {"TOP": create_top_header, "LCPU": create_core_header, "MCPU": create_core_header, "BCPU": create_core_header}
datasheet_list          = []

for temp_file in tqdm(current_temp_files, desc = "Sorting details in temp_* files"):
    ### Skip python script within directory
    if "txt" in temp_file:
        open_file_scan = open(temp_file, "r")
        for line in tqdm(open_file_scan, sec = "Extract data from temp_* file line by line"):
            ### Splitting file lines to variables as per need
            line_split = line.split()
            file_path  = line_split[0]

            if any(check in file_path for check in temperature_list):
                leakage_power = line_split [6]
            else:
                switching_power = line_split[6]
                internal_power  = line_split[12]

            file_path_split = file_path.split("/")
            run_name        = file_path_split[2]
            rpt_name        = file_path_split[6]

            dataframe_dict, hierarchy_name, cell_level = hierarchy_name_search(dataframe_dict, rpt_name, hierarchy_2d_list, cell_levels)
            power_rail                                 = power_rail_search(rpt_name)
            temperature, sort_type                     = leakage_dynamic_sort(rpt_name)

            ### Sort grepped leakage data
            if sort_type == "leakage":
                #### Initialize class objects when first needed
                if hierarchy_name is "TOP":
                    for key in dataframe_dict.keys():
                        if "TOP" in key:
                            new_hierarchy_list = "top_leakage_datalist"

                            if new_hierarchy_list not in datasheet_list:
                                dataframe_dict[key]["leakage_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                datasheet_list.append(new_hierarchy_list)
                        
                        dataframe_dict[key]["leakage_list_class_inst"] = init_data_dump(dataframe_dict[key]["leakage_list_class_isnt"], power_rail, run_name, temperature, temperature_list, temperature_buffer, leakage_power, 0, 0)
                elif hierarchy_name is "LCPU":
                    for key in dataframe_dict.keys():
                        for lcpu_num in range(int(lcpu_number)):
                            key_checker = "LCPU" + str(lcpu_num)

                            if new_hierarchy_list not in datasheet_list:
                                dataframe_dict[key]["leakage_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name, cell_level)
                                datasheet_list.append(new_hierarchy_list)

                            if key not in used_header_list:
                                used_header_list.append(key)

                            dataframe_dict[key]["leakage_list_class_inst"] = init_data_dump(dataframe_dict[key]["leakage_list_class_isnt"], power_rail, run_name, temperature, temperature_list, temperature_buffer, leakage_power, 0, 0)
                elif hierarchy_name is "BCPU":
                    for key in dataframe_dict.keys():
                        for bcpu_num in range(int(bcpu_number)):
                            key_checker = "BCPU" + str(bcpu_num)

                            if new_hierarchy_list not in datasheet_list:
                                dataframe_dict[key]["leakage_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name, cell_level)
                                datasheet_list.append(new_hierarchy_list)

                            if key not in used_header_list:
                                used_header_list.append(key)

                            dataframe_dict[key]["leakage_list_class_inst"] = init_data_dump(dataframe_dict[key]["leakage_list_class_isnt"], power_rail, run_name, temperature, temperature_list, temperature_buffer, leakage_power, 0, 0)
                else:
                    print("")
                    print("")
                    print("Current script does not support hierarchy name: ", hierarchy_name)
                    print("Please either modify the script to fit new hierarchy name or highlight issue to owner")
            ### Sort grepped dynamic data
            elif sort_type is "dynamic":
                #### Initialize class objects when first needed
                if hierarchy_name is "TOP":
                    for key in dataframe_dict.keys():
                        if "TOP" in key:
                            new_hierarchy_list = "top_dynamic_datalist"

                            if new_hierarchy_list not in datasheet_list:
                                if hierarchy_name in hierarchy_dict:
                                    dataframe_dict[key]["dynamic_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                    datasheet_list.append(new_hierarchy_list)
                            
                            dataframe_dict[key]["ddynamic_list_class_inst"] = init_data_dump(dataframe_dict[key]["dynamic_list_class_isnt"], power_rail, run_name, 0, 0, 0, 0, switching_power, internal_power)
                elif hierarchy_name is "LCPU":
                    for key in dataframe_dict.keys():
                        for lcpu_num in range(int(lcpu_number)):
                            key_checker = "LCPU" + str(lcpu_num)
                            
                            if key_checker in key:
                                new_hierarchy_list = "lcpu_" + str(lcpu_num) + "_dynamic_datalist"

                                if new_hierarchy_list not in datasheet_list:
                                    if hierarchy_name in hierarchy_dict:
                                        dataframe_dict[key]["dynamic_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name, cell_level)
                                        datasheet_list.append(new_hierarchy_list)

                                if key not in used_header_list:
                                    used_header_list.append(key)

                                dataframe_dict[key]["dynamic_list_class_inst"] = init_data_dump(dataframe_dict[key]["dynamic_list_class_isnt"], power_rail, run_name, 0, 0, 0, 0, switching_power, internal_power)
                elif hierarchy_name is "BCPU":
                    for key in dataframe_dict.keys():
                        for bcpu_num in range(int(bcpu_number)):
                            key_checker = "BCPU" + str(bcpu_num)

                            if key_checker in key:
                                new_hierarchy_list = "bcpu_" + str(bcpu_num) + "_dynamic_datalist"

                                if new_hierarchy_list not in datasheet_list:
                                    if hierarchy_name in hierarchy_dict:
                                        dataframe_dict[key]["dynamic_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name, cell_level)
                                        datasheet_list.append(new_hierarchy_list)

                                if key not in used_header_list:
                                    used_header_list.append(key)

                                dataframe_dict[key]["dynamic_list_class_inst"] = init_data_dump(dataframe_dict[key]["dynamic_list_class_isnt"], power_rail, run_name, 0, 0, 0, 0, switching_power, internal_power)
                else:
                    print("")
                    print("")
                    print("Current script does not support hierarchy name: ", hierarchy_name)
                    print("Please either modify script to fit new hierarchy name or highlight issue to owner")
            else:
                print("Please check script and temp files as listed sort_type is invalid!!!")
                break


## Convert datalist to dataframe and clean up data cells
for key in dataframe_dict.keys():
    dataframe_dict[key]["leakage_df"] = pd.DataFrame(dataframe_dict[key]["leakage_list_class_inst"].data_list)
    dataframe_dict[key]["dynamic_df"] = pd.DataFrame(dataframe_dict[key]["dynamic_list_class_inst"].data_list)

    dataframe_dict[key]["leakage_df"].reset_index(inplace=True, drop=True)
    dataframe_dict[key]["dynamic_df"].drop([1], axis=0, inplace=True)
    dataframe_dict[key]["dynamic_df"].reset_index(inplace=True, drop=True)

    for col in range(len(dataframe_dict[key]["leakage_df"].columns)):
        for row in range(len(dataframe_dict[key]["leakage_df"][col])):
            if (dataframe_dict[key]["leakage_df"][col][row] is "" or dataframe_dict[key]["leakage_df"][col][row is None] and row > 1):
                dataframe_dict[key]["leakage_df"][col][row] = 0
        
        if dataframe_dict[key]["leakage_df"][col][0] is None:
            dataframe_dict[key]["leakage_df"].drop(columns=[col], inplace=True)

    for col in range(len(dataframe_dict[key]["dynamic_df"].columns)):
        for row in range(len(dataframe_dict[key]["dynamic_df"][col])):
            if (dataframe_dict[key]["dynamic_df"][col][row] is "" or dataframe_dict[key]["dynamic_df"][col][row is None] and row > 1):
                dataframe_dict[key]["dynamic_df"][col][row] = 0
        
        if dataframe_dict[key]["dynamic_df"][col][0] is None:
            dataframe_dict[key]["dynamic_df"].drop(columns=[col], inplace=True)


# Third part -> Generating top_only header dataframe
## Check if provided cores matche processed dataframes
lcpu_number, alt_lcpu_number = cpu_num_checker(lcpu_number, "LCPU", dataframe_dict)

if int(mcpu_number) != 0:
    print("")
    print("")
    print("MCPU cores are not supported in this script yet")
    print("Please either edit this script manually or consult owner for MCPU addition")
#mcpu_number, alt_mcpu_number = cpu_num_checker(mcpu_number, "MCPU", dataframe_dict)

bcpu_number, alt_bcpu_number = cpu_num_checker(bcpu_number, "BCPU", dataframe_dict)


## Remove row index and column header from dataframe
dataframe_dict["TOP"]["clean_leakage_df"] = top_dataframe_cleanup(dataframe_dict["TOP"]["leakage_df"])
dataframe_dict["TOP"]["clean_dynamic_df"] = top_dataframe_cleanup(dataframe_dict["TOP"]["dynamic_df"])

if any("LCPU" in key for key in dataframe_dict.keys()):
    dataframe_dict = top_only_df_calculation(lcpu_number, alt_lcpu_number, 0, "LCPU", dataframe_dict)
#if any("MCPU" in key for key in dataframe_dict.keys()):
#    dataframe_dict = top_only_df_calculation(mcpu_number, alt_mcpu_number, 0, "MCPU", dataframe_dict)
if any("BCPU" in key for key in dataframe_dict.keys()):
    dataframe_dict = top_only_df_calculation(bcpu_number, alt_bcpu_number, 0, "BCPU", dataframe_dict)


## Process top_only dataframe row index and column header
if any("TOP_only" in key for key in dataframe_dict.keys()):
    print("")
    print("")
    print("Check why dataframe_dict already has TOP_only key present prior to data dumping")
else:
    dataframe_dict["TOP_only"] = {}
    dataframe_dict             = add_row_col_dataframe(dataframe_dict)


## Remove "Temp" key in dataframe_dict to prevent misprint
dataframe_dict.pop("Temp", None)


# Fourth part -> Writing into excel file
writer = pd.ExcelWriter(output_file_name, engine = "xlsxwriter")

for key in dataframe_dict.keys():
    leakage_sheet_name = key + "_leakage"
    dynamic_sheet_name = key + "_dynamic"
    dataframe_dict[key]["leakage_df"].to_excel(writer, sheet_name = leakage_sheet_name)
    dataframe_dict[key]["dynamic_df"].to_excel(writer, sheet_name = dynamic_sheet_name)

writer.save()


# Fifth part - > Clean up temp_* files
for temp_file in tqdm(current_temp_files, desc = "Removing temp_* files in current path"):
    if "txt" in temp_file:
        remove(temp_file)


# Runtime calculation
end_time     = time.time()
duration_sec = end_time - start_time

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
print("All power data dumping completed")
print("Process took ", duration, tag, "to finish")
print("Please check outputs here: ", output_file_name)