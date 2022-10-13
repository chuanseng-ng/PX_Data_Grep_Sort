from get_px_power.define.get_classes import *
from tqdm import tqdm
import pandas as pd
import numpy as np
import re

## Grep leakage line details
def grep_leakage(keyword_file, write_file, temperature_list):
    search_term     = "Cell Leakage Power"
    open_file_read  = open(keyword_file, "r")
    open_file_write = open(write_file, "a")

    if any(check in keyword_file for check in temperature_list):
        for line in tqdm(open_file_read, desc="Grep leakage keyword in file"):
            if re.search(search_term, line):
                temp_input = keyword_file + " , " + line
                open_file_write.write(temp_input)
    
    open_file_write.close()

## Grep internal & switching line details
def grep_dynamic(keyword_file, write_file, temperature_list):
    search_internal_term  = "Cell Internal Power"
    search_switching_term = "Net Switching Power"
    open_file_read        = open(keyword_file, "r")
    open_file_write       = open(write_file, "a")
    temp_input            = keyword_file

    if not(any(check in keyword_file for check in temperature_list)):
        for line in tqdm(open_file_read, desc="Grep internal keyword in file"):
            if re.search(search_switching_term, line):
                sub_input    = re.sub('\(.+\)', '', line)
                edited_input = sub_input.strip()
                temp_input   = temp_input + " , " + edited_input
            elif re.search(search_internal_term, line):
                temp_input   = temp_input + " , " + line
        open_file_write.write(temp_input)

    open_file_write.close()

## Extract power rail details
def power_rail_search(report_name):
    search_result = re.search('UPF_(.+?)_rail', report_name).group(1)

    return search_result

## Split dynamic & leakage files
def leakage_dynamic_sort(report_name):
    if re.search('pwr(.+?).rpt', report_name) != None:
        search_result = re.search('pwr(.+?).rpt', report_name).group(1)
        temperature   = search_result.split("_")[4]
        sort_type     = "leakage"
    else:
        temperature = ""
        sort_type   = "dynamic"

    return temperature, sort_type

## Search for lowest hierarchy name in report name
def hierarchy_name_search(df_dict, report_name, hier_2d_list, cell_lvls):
    for hier_list in tqdm(hier_2d_list, desc="Go thru lists within 2D list of lists for hierarchy names"):
        if any(hier in report_name for hier in hier_list):
            gen_hier_name = hier_list[0]
    
    for cell_lvl in cell_lvls:
        if cell_lvl in report_name:
            report_extract_cell_lvl = cell_lvl

    extract_core_num = report_extract_cell_lvl.split("_")[1]

    if gen_hier_name is "TOP":
        dict_checker                = gen_hier_name
        check_leakage_datalist_name = gen_hier_name.lower() + "_leakage_datalist"
        check_dynamic_datalist_name = gen_hier_name.lower() + "_dynamic_datalist"
    else:
        dict_checker                = gen_hier_name + extract_core_num
        check_leakage_datalist_name = gen_hier_name.lower() + "_" + extract_core_num + "_leakage_datalist"
        check_dynamic_datalist_name = gen_hier_name.lower() + "_" + extract_core_num + "_dynamic_datalist"
    
    if dict_checker not in df_dict:
        df_dict[dict_checker] = {
            "leakage_list": check_leakage_datalist_name,
            "dynamic_list": check_dynamic_datalist_name
        }

    return df_dict, gen_hier_name, report_extract_cell_lvl

## Generate top header class object
def create_top_header(hier_name):
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
def create_core_header(hier_name, cell_lvl):
    core_header             = hier_name
    updated_core_header      = core_header + "_" + cell_lvl.split("_")[1]
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
def create_lcpu_header(hier_name, cell_lvl):
    lcpu_header             = "LCPU"
    updated_lcpu_header     = lcpu_header + "_" + cell_lvl.split("_")[1]
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
def create_mcpu_header(hier_name, cell_lvl):
    mcpu_header             = "mcpu"
    updated_mcpu_header     = mcpu_header + "_" + cell_lvl.split("_")[1]
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

## Generate MCPU header class object
def create_bcpu_header(hier_name, cell_lvl):
    bcpu_header             = "bcpu"
    updated_bcpu_header     = bcpu_header + "_" + cell_lvl.split("_")[1]
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
def data_dumping(datalist, power_rail, run_name, temperature, temperature_buff, leakage_power, switching_power, internal_power):
    for key, value in datalist.power_rail_dict.items():
        if value == power_rail:
            if temperature != 0:
                temp_rail_position = int(key)
            else:
                temp_x_position = int(key)
    
    if temperature != 0:
        for count in (range(temp_rail_position, temp_rail_position + temperature_buff)):
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
def init_data_dump(datalist, power_rail, run_name, temperature, temperature_list, temperature_buff, leakage_power, switching_power, internal_power):
    if run_name not in datalist.run_name_dict.values():
        run_name_list = []
        run_name_list.append(run_name)

        datalist.data_list.append(run_name_list)
        datalist.run_name_dict[datalist.run_name_count] = run_name
        datalist.run_name_count                         = str(int(datalist.run_name_count) + 1)

        if power_rail in datalist.power_rail_dict.values():
            for _ in tqdm(range(int(list(datalist.power_rail_dict.keys())[-1]) + 5), desc="Filling empty buffer in new run name row after power rail filled"):
                datalist.data_list[int(datalist.run_name_count)].append("")

    if power_rail not in datalist.power_rail_dict.values():
        datalist.data_list[0].append(power_rail)
        datalist.power_rail_dict[datalist.run_name_count] = power_rail

        if temperature != 0:
            datalist.power_rail_position = str(int(datalist.power_rail_position) + int(temperature_buff))
        else:
            datalist.power_rail_position = str(int(datalist.power_rail_position) + 1)

        if temperature != 0:
            for _ in tqdm(range(int(temperature_buff)), desc="Filling empty buffer in power rail row"):
                datalist.data_list[0].append("")
            
            if len(datalist.data_list[int(datalist.run_name_count)]) == len(datalist.data_list[0]) - 5:
                for _ in tqdm(range(temperature_buff), desc="Filling empty buffer in run name row"):
                    datalist.data_list[int(datalist.run_name_count)].append("")
            else:
                for _ in tqdm(range(int(list(datalist.power_rail_dict.keys())[-1]) + 5), desc="Filling empty buffer in new run name row after addition of new power rail"):
                    datalist.data_list[int(datalist.run_name_count)].append("")

            datalist.data_list[1].extend(temperature_list)
        else:
            if len(datalist.data_list[int(datalist.run_name_count)]) == len(datalist.data_list[0]) - 1:
                datalist.data_list[int(datalist.run_name_count)].append("")
            else:
                for _ in tqdm(range(int(list(datalist.power_rail_dict.keys())[-1]) + 1), desc="Filling empty buffer in new run name row after addition of new power rail"):
                    datalist.data_list[int(datalist.run_name_count)].append("")

    if temperature != 0:
        updated_datalist = data_dumping(datalist, power_rail, run_name, temperature, temperature_buff, leakage_power, 0, 0)
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
    dataframe_col_num      = len(dataframe.columns)
    add_count              = 0

    if any(item is None for item in dataframe.iloc[0, :]):
        for count in range(dataframe_col_num - 1):
            while count + add_count < dataframe_col_num and dataframe.iloc[0, count] is None:
                add_count = add_count + 1
                dataframe_iloc.drop(columns = dataframe_iloc.columns[count], inplace = True)
            
            if count + add_count == dataframe_col_num - 1:
                break
    else:
        dataframe_iloc = dataframe

    dataframe_iloc.reset_index(inplace = True, drop = True)

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
    dataframe_col_num      = len(dataframe.columns)
    add_count              = 0

    if any(item is None for item in dataframe.iloc[0, 1]):
        for count in range(dataframe_col_num - 1):
            while count + add_count < dataframe_col_num and dataframe.iloc[0, count + 1] is None:
                add_count = add_count + 1
                if dataframe.iloc[0, count] is None:
                    dataframe_iloc.drop(columns = dataframe_iloc.columns[count], inplace = True)
            
            if count + add_count == dataframe_col_num - 1:
                break
    else:
        dataframe_iloc = dataframe

    dataframe_iloc.reset_index(inplace = True, drop = True)

    if "Temperature" in dataframe_iloc[0][1]:
        temp_dataframe = dataframe_iloc.drop([0, 1], axis = 0)
    else:
        temp_dataframe = dataframe_iloc.drop([0], axis = 0)

    clean_dataframe = temp_dataframe.drop(columns = 0)

    return clean_dataframe

## Perfrom arithmetic operations on TOP dataframe to generate TOP_only dataframe
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
                    sub_key = key

    if "Temp" not in dataframe_dict.keys():
        dataframe_dict["Temp"] = {}
        dataframe_dict["Temp"]["leakage_df"] = dataframe_dict["TOP"]["clean_leakage_df"] - \
                                                dataframe_dict[main_key]["clean_leakage_df"] - \
                                                int(alt_cpu_number)*dataframe_dict[sub_key]["clean_leakage_df"]
        dataframe_dict["Temp"]["dynamic_df"] = dataframe_dict["TOP"]["clean_dynamic_df"] - \
                                                dataframe_dict[main_key]["clean_dynamic_df"] - \
                                                int(alt_cpu_number)*dataframe_dict[sub_key]["clean_dynamic_df"]
    else:
        dataframe_dict["Temp"]["leakage_df"] = dataframe_dict["Temp"]["leakage_df"] - \
                                                dataframe_dict[main_key]["clean_leakage_df"] - \
                                                int(alt_cpu_number)*dataframe_dict[sub_key]["clean_leakage_df"]
        dataframe_dict["Temp"]["dynamic_df"] = dataframe_dict["Temp"]["dynamic_df"] - \
                                                dataframe_dict[main_key]["clean_dynamic_df"] - \
                                                int(alt_cpu_number)*dataframe_dict[sub_key]["clean_dynamic_df"]

    return dataframe_dict

## Populate row index and column header in top_only dataframe
def add_row_col_dataframe(dataframe_dict):
    top_col_only_leakage_series = (dataframe_dict["TOP"]["leakage_df"].drop([0, 1], axis = 0)).iloc[:, 0]
    top_col_only_dynamic_series = (dataframe_dict["TOP"]["dynamic_df"].drop([0], axis = 0)).iloc[:, 0]

    top_col_only_leakage_dataframe       = top_col_only_leakage_series.to_frame()
    top_col_only_dynamic_dataframe       = top_col_only_dynamic_series.to_frame()
    top_no_header_only_leakage_dataframe = top_col_only_leakage_dataframe.join(dataframe_dict["Temp"]["leakage_df"])
    top_no_header_only_dynamic_dataframe = top_col_only_dynamic_dataframe.join(dataframe_dict["Temp"]["dynamic_df"])

    top_row_only_leakage_dataframe_trans = dataframe_dict["TOP"]["leakage_df"].T
    top_row_only_dynamic_dataframe_trans = dataframe_dict["TOP"]["dynamic_df"].T
    top_row_only_leakage_dataframe_trans.drop(top_row_only_leakage_dataframe_trans.iloc[:, 2:-1], inplace = True, axis = 1)
    top_row_only_dynamic_dataframe_trans.drop(top_row_only_dynamic_dataframe_trans.iloc[:, 1:-1], inplace = True, axis = 1)

    top_row_only_leakage_dataframe_trans_iloc = top_row_only_leakage_dataframe_trans.iloc[:, :-1]
    top_row_only_dynamic_dataframe_trans_iloc = top_row_only_dynamic_dataframe_trans.iloc[:, :-1]

    top_no_header_only_leakage_dataframe_trans = top_no_header_only_leakage_dataframe.T
    top_no_header_only_dynamic_dataframe_trans = top_no_header_only_dynamic_dataframe.T
    top_only_leakage_dataframe_trans           = pd.concat([top_row_only_leakage_dataframe_trans_iloc, top_no_header_only_leakage_dataframe_trans], axis = 1)
    top_only_dynamic_dataframe_trans           = pd.concat([top_row_only_dynamic_dataframe_trans_iloc, top_no_header_only_dynamic_dataframe_trans], axis = 1)
    dataframe_dict["TOP_only"]["leakage_df"]   = top_only_leakage_dataframe_trans.T
    dataframe_dict["TOP_only"]["dynamic_df"]   = top_only_dynamic_dataframe_trans.T

    dataframe_dict["TOP_only"]["leakage_df"][0][0] = "TOP_only"
    dataframe_dict["TOP_only"]["dynamic_df"][0][0] = "TOP_only"

    return dataframe_dict