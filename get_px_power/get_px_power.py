from asyncore import file_dispatcher
from distutils.file_util import write_file
from doctest import run_docstring_examples
from re import I
from get_px_power.define.get_functions import grep_leakage, grep_dynamic, power_rail_search, leakage_dynamic_sort, \
                                        create_top_header, create_core_header, hierarchy_name_search, \
                                        init_data_dump, cpu_num_checker, top_dataframe_cleanup, \
                                        top_only_df_calculation, add_row_col_dataframe
from os import listdir, stat, remove
from os.path import isfile, join
from tqdm import tqdm
from glob import glob
import pandas as pd
import numpy as np
import re
import sys
import xlsxwriter

def get_px_power(directory_keyword, output_file_name, lcpu_num, mcpu_num, bcpu_num):
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

    ## Remove exsiting temp_* files to avoid overlap/conflict
    for temp_file in tqdm(existing_temp_files, desc = "Removing existing temp_* files"):
        if "txt" in temp_file:
            remove(temp_file)
    
    if len(keyword_directories) == 0:
        print("Keyword not present in ../all_out path")
        print("Please check the current ../all_out path for a valid keyword")
        sys.exit(1)

    for directory in tqdm(keyword_directories, desc = "Keyword directory UPF_DVDD files breakdown"):
        keyword_file_path = directory + "/report/*/active/UPF_DVDD*.rpt"
        upf_dvdd_files    = glob(keyword_file_path)
        write_file        = "temp_" + directory.split("/")[2] + ".txt"

        temp_clean_file = open(write_file, "w+")
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

    temperature_buffer = 5
    used_header_list   = ["TOP"]
    hierarchy_dict     = {"TOP": create_top_header, "LCPU": create_core_header, "MCPU": create_core_header, "BCPU": create_core_header}
    datasheet_list     = []

    for temp_file in tqdm(current_temp_files, desc = "Sorting details in temp_* files"):
        if "txt" in temp_file:
            open_file_scan = open(temp_file, "r")
            for line in tqdm(open_file_scan, desc = "Extract data from temp_* file line by line"):
                ## Splitting file lines to variables as per need
                line_split = line.split()
                file_path  = line_split[0]
                if any(check in file_path for check in temperature_list):
                    leakage_power = line_split[6]
                else:
                    switching_power = line_split[6]
                    internal_power  = line_split[12]

                file_path_split = file_path.split("/")
                run_name        = file_path_split[2]
                rpt_name        = file_path_split[6]

                dataframe_dict, hierarchy_name, cell_level = hierarchy_name_search(dataframe_dict, rpt_name, hierarchy_2d_list, cell_levels)
                power_rail                                 = power_rail_search(rpt_name)
                temperature, sort_type                     = leakage_dynamic_sort(rpt_name)

                ## Sort grepped leakage data
                if sort_type == "leakage":
                    ### Initialize class objects when first needed
                    if hierarchy_name is "TOP":
                        for key in dataframe_dict.keys():
                            if "TOP" in key:
                                new_hierarchy_list = "top_leakage_datalist"
                                if new_hierarchy_list not in datasheet_list:
                                    if hierarchy_name in hierarchy_dict:
                                        dataframe_dict[key]["leakage_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                        datasheet_list.append(new_hierarchy_list)
                                
                                dataframe_dict[key]["leakage_list_class_inst"] = init_data_dump(dataframe_dict[key]["leakage_list_class_inst"], \
                                                                                                power_rail, run_name, temperature, temperature_list, \
                                                                                                temperature_buffer, leakage_power, 0, 0)

                    elif hierarchy_name is "LCPU":
                        for key in dataframe_dict.keys():
                            for lcpu_cnt in range(int(lcpu_num)):
                                key_checker = "LCPU" + str(lcpu_cnt)
                                if key_checker in key:
                                    new_hierarchy_list = "lcpu" + str(lcpu_cnt) + "_leakage_datalist"
                                    if new_hierarchy_list not in datasheet_list:
                                        if hierarchy_name in hierarchy_dict:
                                            dataframe_dict[key]["leakage_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                            datasheet_list.append(new_hierarchy_list)
                                    
                                    if key not in used_header_list:
                                        used_header_list.append(key)

                                    dataframe_dict[key]["leakage_list_class_inst"] = init_data_dump(dataframe_dict[key]["leakage_list_class_inst"], \
                                                                                                    power_rail, run_name, temperature, temperature_list, \
                                                                                                    temperature_buffer, leakage_power, 0, 0)
                    
                    elif hierarchy_name is "BCPU":
                        for key in dataframe_dict.keys():
                            for bcpu_cnt in range(int(bcpu_num)):
                                key_checker = "bcpu" + str(bcpu_cnt)
                                if key_checker in key:
                                    new_hierarchy_list = "bcpu" + str(bcpu_cnt) + "_leakage_datalist"
                                    if new_hierarchy_list not in datasheet_list:
                                        if hierarchy_name in hierarchy_dict:
                                            dataframe_dict[key]["leakage_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                            datasheet_list.append(new_hierarchy_list)
                                    
                                    if key not in used_header_list:
                                        used_header_list.append(key)

                                    dataframe_dict[key]["leakage_list_class_inst"] = init_data_dump(dataframe_dict[key]["leakage_list_class_inst"], \
                                                                                                    power_rail, run_name, temperature, temperature_list, \
                                                                                                    temperature_buffer, leakage_power, 0, 0)

                    else:
                        print("")
                        print("")
                        print("Current script does not support hierarchy name: ", hierarchy_name)
                        print("Please either modify script to fit new hierarchy name or highlight issue to owner")

                ## Sort grepped dynamic data
                elif sort_type == "dynamic":
                    ### Initialize class objects when first needed
                    if hierarchy_name is "TOP":
                        for key in dataframe_dict.keys():
                            if "TOP" in key:
                                new_hierarchy_list = "top_dynamic_datalist"
                                if new_hierarchy_list not in datasheet_list:
                                    if hierarchy_name in hierarchy_dict:
                                        dataframe_dict[key]["dynamic_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                        datasheet_list.append(new_hierarchy_list)
                                
                                dataframe_dict[key]["dynamic_list_class_inst"] = init_data_dump(dataframe_dict[key]["dynamic_list_class_inst"], \
                                                                                                power_rail, run_name, 0, 0, 0, 0, switching_power, internal_power)
                    
                    elif hierarchy_name is "LCPU":
                        for key in dataframe_dict.keys():
                            for lcpu_cnt in range(int(lcpu_num)):
                                key_checker = "LCPU" + str(lcpu_cnt)
                                if key_checker in key:
                                    new_hierarchy_list = "lcpu" + str(lcpu_cnt) + "_dynamic_datalist"
                                    if new_hierarchy_list not in datasheet_list:
                                        if hierarchy_name in hierarchy_dict:
                                            dataframe_dict[key]["dynamic_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                            datasheet_list.append(new_hierarchy_list)
                                    
                                    if key not in used_header_list:
                                        used_header_list.append(key)

                                    dataframe_dict[key]["dynamic_list_class_inst"] = init_data_dump(dataframe_dict[key]["dynamic_list_class_inst"], \
                                                                                                    power_rail, run_name, 0, 0, 0, 0, switching_power, internal_power)

                    elif hierarchy_name is "BCPU":
                        for key in dataframe_dict.keys():
                            for bcpu_cnt in range(int(bcpu_num)):
                                key_checker = "bcpu" + str(bcpu_cnt)
                                if key_checker in key:
                                    new_hierarchy_list = "bcpu" + str(bcpu_cnt) + "_dynamic_datalist"
                                    if new_hierarchy_list not in datasheet_list:
                                        if hierarchy_name in hierarchy_dict:
                                            dataframe_dict[key]["dynamic_list_class_inst"] = hierarchy_dict[hierarchy_name](hierarchy_name)
                                            datasheet_list.append(new_hierarchy_list)
                                    
                                    if key not in used_header_list:
                                        used_header_list.append(key)

                                    dataframe_dict[key]["dynamic_list_class_inst"] = init_data_dump(dataframe_dict[key]["dynamic_list_class_inst"], \
                                                                                                    power_rail, run_name, 0, 0, 0, 0, switching_power, internal_power)

                    else:
                        print("")
                        print("")
                        print("Current script does not support hierarchy name: ", hierarchy_name)
                        print("Please either modify script to fit new hierarchy name or highlight issue to owner")
                
                else:
                    print("Please check script and temp files as listed sort type is invalid")
                    break

    # Convert datalist to dataframe and clean up data cells
    for key in dataframe_dict.keys():
        dataframe_dict[key]["leakage_df"] = pd.DataFrame(dataframe_dict[key]["leakage_list_class_inst"].data_list)
        dataframe_dict[key]["dynamic_df"] = pd.DataFrame(dataframe_dict[key]["dynamic_list_class_inst"].data_list)

        dataframe_dict[key]["leakage_df"].reset_index(inplace = True, drop = True)
        dataframe_dict[key]["dynamic_df"].drop([1], axis = 0, inplace = True)
        dataframe_dict[key]["dynamic_df"].reset_index(inplace = True, drop = True)

        for col in range(len(dataframe_dict[key]["leakage_df"].columns)):
            for row in range(len(dataframe_dict[key]["leakage_df"][col])):
                if (dataframe_dict[key]["leakage_df"][col][row] is "" or dataframe_dict[key]["leakage_df"][col][row] is None) and row > 1:
                    dataframe_dict[key]["leakage_df"][col][row] = 0
            
            if dataframe_dict[key]["leakage_df"][col][0] is None:
                dataframe_dict[key]["leakage_df"].drop(columns = [col], inplace = True)

        for col in range(len(dataframe_dict[key]["dynamic_df"].columns)):
            for row in range(len(dataframe_dict[key]["dynamic_df"][col])):
                if (dataframe_dict[key]["dynamic_df"][col][row] is "" or dataframe_dict[key]["dynamic_df"][col][row] is None) and row > 1:
                    dataframe_dict[key]["dynamic_df"][col][row] = 0
            
            if dataframe_dict[key]["dynamic_df"][col][0] is None:
                dataframe_dict[key]["dynamic_df"].drop(columns = [col], inplace = True)

    # Third part -> Generating TOP_only header dataframe
    # Check if provided cores matches with processed dataframes
    lcpu_num, alt_lcpu_num = cpu_num_checker(lcpu_num, "LCPU", dataframe_dict)

    if int(mcpu_num) != 0:
        print("")
        print("")
        print("MCPU cores are not supported in this script yet")
        print("Please either edit this script or consult owner for this feature")

    bcpu_num, alt_bcpu_num = cpu_num_checker(bcpu_num, "BCPU", dataframe_dict)

    # Remove row index and column header from dataframe
    dataframe_dict["TOP"]["clean_leakage_df"] = top_dataframe_cleanup(dataframe_dict["TOP"]["leakage_df"])
    dataframe_dict["TOP"]["clean_dynamic_df"] = top_dataframe_cleanup(dataframe_dict["TOP"]["dynamic_df"])

    if any("LCPU" in key for key in dataframe_dict.keys()):
        dataframe_dict = top_only_df_calculation(lcpu_num, alt_lcpu_num, 0, "LCPU", dataframe_dict)
    if any("BCPU" in key for key in dataframe_dict.keys()):
        dataframe_dict = top_only_df_calculation(bcpu_num, alt_bcpu_num, lcpu_num, "BCPU", dataframe_dict)

    # Process top_only dataframe row index and column header
    if any("TOP_only" in key for key in dataframe_dict.keys()):
        print("")
        print("")
        print("Check why dataframe_dict already has TOP_only key present prior to data dumping")
    else:
        dataframe_dict["TOP_only"] = {}
        dataframe_dict             = add_row_col_dataframe(dataframe_dict)

    # Remove "Temp" key in dataframe_dict to prevent misprint
    dataframe_dict.pop("Temp", None)

    # Fourth part -> Writing into excel
    writer = pd.ExcelWriter(output_file_name, engine = "xlsxwriter")
    for key in dataframe_dict.keys():
        leakage_sheet_name = key + "_leakage"
        dynamic_sheet_name = key + "_dynamic"
        dataframe_dict[key]["leakage_df"].to_excel(writer, sheet_name = leakage_sheet_name)
        dataframe_dict[key]["dynamic_df"].to_excel(writer, sheet_name = dynamic_sheet_name)

    writer.save()

    # Fifth part -> Clean up temp_* files
    for temp_file in tqdm(current_temp_files, desc = "Removing temp_* files in current path"):
        if "txt" in temp_file:
            remove(temp_file)