from os import listdir, stat, remove
from os.path import isfile, join
from tqdm import tqdm
from glob import glob
import pandas as pd
import numpy as np
import sys
import time

# Function declaration
## Replace all NaN within cell values with 0 to avoid arithmetic errors
def replace_nan_with_zero(df):
    row_number = len(df)
    col_number = len(df.columns)

    for i in range(2, row_number):
        for j in range(2, col_number):
            if pd.isna(df.iloc[i, j]):
                df.at[i, j-1] = 0
    
    return df

## Remove row index and column header from dataframe
def remove_row_col(df):
    trim_no_header_df = df.drop([0, 1], axis = 0)
    trim_df           = (trim_no_header_df.iloc[:, 1:]).drop(columns = 0)

    return trim_df

## Add data from selected power rails together
def sel_data_add(count, curr_sel_index_list, sel_list, trim_df):
    temp_df_list = []

    for iter in range(len(sel_list[count])):
        curr_sel_index         = int(curr_sel_index_list[iter])
        temp_df                = trim_df.iloc[:, (curr_sel_index - 1):(curr_sel_index + 4)]
        sorted_temp_df         = temp_df.reset_index(drop = True)
        sorted_temp_df.columns = pd.RangeIndex(sorted_temp_df.columns.size)
        temp_df_list.append(sorted_temp_df)

    for iter in range(len(temp_df_list)):
        if iter == 0:
            temp_add_df = temp_df_list[iter]
        else:
            temp_add_df = temp_add_df.add(temp_df_list[iter])

    return temp_add_df

## Generate full df with selected power rail data for input header
def df_gen_full(sel_list, power_rail_list, trim_df, df):
    sel_num       = len(sel_list)
    sel_name_list = []
    added_df_list = []

    for count in range(sel_num):
        curr_sel_name        = ""
        curr_sel_index_list = []

        ### Generate new block ehader based on combination of user-selected power rails
        for select in sel_list[count]:
            curr_sel_index = int(select) * 5 + 1
            curr_sel_index_list.append(curr_sel_index)

            if curr_sel_name == "":
                curr_sel_name = power_rail_list[int(select)]
            else:
                curr_sel_name = curr_sel_name + " + " + power_rail_list[int(select)]

        sel_name_list.append(curr_sel_name)
        temp_add_df = sel_data_add(count, curr_sel_index_list, sel_list, trim_df)
        added_df_list.append(temp_add_df)

    data_only_df = added_df_list[0]

    for count in range(1, len(added_df_list)):
        data_only_df = pd.concat([data_only_df, added_df_list[count]], axis = 1)

    data_only_df.columns = pd.RangeIndex(data_only_df.columns.size)

    col_only_series = df[0].drop([0, 1], axis = 0)
    col_only_df     = col_only_series.to_frame()
    col_only_df.reset_index(drop = True, inplace = True)

    no_row_df = pd.concat([col_only_df, data_only_df], axis = 1)

    row_only_series = df.loc[0:1, 0]
    row_only_df     = row_only_series.to_frame()

    temperature_list          = ["25c", "45c", "65c", "85c", "105c"]
    temperature_buffer        = 5
    temp_sel_temperature_list = []

    for count in range(len(sel_name_list)):
        if len(temp_sel_temperature_list) == 0:
            temp_sel_list = []
            temp_sel_list.append(sel_name_list[count])
            temp_sel_temperature_list.append(temp_sel_list)

            for _ in range(temperature_buffer - 1):
                temp_sel_temperature_list[0].append(np.nan)

            temp_sel_temperature_list.append(temperature_list)
        else:
            temp_sel_temperature_list[0].append(sel_name_list[count])

            for _ in range(temperature_buffer - 1):
                temp_sel_temperature_list[0].append(np.nan)
            
            temp_sel_temperature_list[1].extend(temperature_list)

    power_rail_df = pd.DataFrame(temp_sel_temperature_list)

    for count in range(len(power_rail_df.columns)):
        if power_rail_df[count][0] is None:
            power_rail_df.drop(columns = [count], inplace = True)

    complete_row_df = pd.concat([row_only_df, power_rail_df], axis = 1)
    complete_df     = pd.concat([complete_row_df, no_row_df], axis = 0)

    return complete_df


#Ask user for xlsx file name, ideally in same directory
# Default xlsx file name is Power.xlsx
print("Default input xlsx file name is Power.xlsx")
print("Output xlsx file name will be with _select tag as postfix")
print("Default output xlsx file name is Power_select.xlsx")
input_file_name = input("For other names, please provide here: ")
print("")

if not (input_file_name and input_file_name.split):
    input_file_name = 'Power.xlsx'

input_file_name_split = input_file_name.split(".")
output_file_name      = input_file_name_split[0] + "_select.xlsx"

start_time = time.time()

# Read in excel file details into dataframes
all_df_dict = pd.read_excel(input_file_name, sheet_name = None, engine = "openpyxl")
all_df_dict.pop("TOP_leakage", None)
all_df_dict.pop("TOP_dynamic", None)

top_only_df      = all_df_dict.get("TOP_only_leakage")
top_only_df      = replace_nan_with_zero(top_only_df)
trim_top_only_df = remove_row_col(top_only_df)

if "LCPU0_leakage" in all_df_dict:
    lcpu_0_df      = all_df_dict.get("LCPU0_leakage")
    lcpu_0_df      = replace_nan_with_zero(lcpu_0_df)
    trim_lcpu_0_df = remove_row_col(lcpu_0_df)
if "LCPU1_leakage" in all_df_dict:
    lcpu_1_df      = all_df_dict.get("LCPU1_leakage")
    lcpu_1_df      = replace_nan_with_zero(lcpu_1_df)
    trim_lcpu_1_df = remove_row_col(lcpu_1_df)
if "BCPU6_leakage" in all_df_dict:
    bcpu_6_df      = all_df_dict.get("BCPU6_leakage")
    bcpu_6_df      = replace_nan_with_zero(bcpu_6_df)
    trim_bcpu_6_df = remove_row_col(bcpu_6_df)
if "BCPU7_leakage" in all_df_dict:
    bcpu_7_df      = all_df_dict.get("BCPU7_leakage")
    bcpu_7_df      = replace_nan_with_zero(bcpu_7_df)
    trim_bcpu_7_df = remove_row_col(bcpu_7_df)

# Extract power_rail info from dataframes
power_rail_list = []

for item in top_only_df.iloc[0, :]:
    if not pd.isna(item):
        power_rail_list.append(item)

power_rail_list.pop(0)
power_rail_list.pop(0)

# Show user available power_rail to choose from based on input xlsx file
print("Here are the available power rails to choose from: ")
for count in range(len(power_rail_list)):
    print(count, "- ", power_rail_list[count])

print("")
print("Please input the selection number for each calculation")
print("Each selection should be separated by a space")
print("Each selection should only be selected once in each run")
print("Once all calculation selections are done, please press enter again")
print("")

max_power_rail_count = len(power_rail_list)
sel_list             = []
stop_sel             = 0

user_input_start_time = time.time()

# Ask user to provide sets of power_rail, if any
while not stop_sel:
    temp_sel_list = []
    sel_input     = input("Please provide selection numbers: ")

    if sel_input and sel_input.split:
        sel_input_split = sel_input.strip().split(" ")

        for item in sel_input_split:
            if any(item in sorted_item for sorted_item in sel_list):
                print("An input selection has been repeated -> ", item)
                print("Please only choose each input selection once")
                sys.ext(1)
            elif int(item) > int(max_power_rail_count - 1):
                print("Highest input selection number is ", max_power_rail_count - 1)
                print("Current input selection number of ", item, " exceeds that")
                print("Please choose within the input selection range")
                sys.exit(1)
            else:
                temp_sel_list.append(item)

        sel_list.append(temp_sel_list)
    else:
        stop_sel = 1

user_input_end_time = time.time()

top_only_final_df = df_gen_full(sel_list, power_rail_list, trim_top_only_df, top_only_df)
if "LCPU0_leakage" in all_df_dict:
    lcpu_0_final_df = df_gen_full(sel_list, power_rail_list, trim_lcpu_0_df, lcpu_0_df)
if "LCPU1_leakage" in all_df_dict:
    lcpu_1_final_df = df_gen_full(sel_list, power_rail_list, trim_lcpu_1_df, lcpu_1_df)
if "BCPU6_leakage" in all_df_dict:
    bcpu_6_final_df = df_gen_full(sel_list, power_rail_list, trim_bcpu_6_df, bcpu_6_df)
if "BCPU7_leakage" in all_df_dict:
    bcpu_7_final_df = df_gen_full(sel_list, power_rail_list, trim_bcpu_7_df, bcpu_7_df)


# Writing into excel file
writer = pd.ExcelWriter(output_file_name, engine = "xlsxwriter")
top_only_final_df.to_excel(writer, sheet_name = "TOP_only_leakage")
if "LCPU0_leakage" in all_df_dict:
    lcpu_0_final_df.to_excel(writer, sheet_name = "LCPU0_leakage")
if "LCPU1_leakage" in all_df_dict:
    lcpu_1_final_df.to_excel(writer, sheet_name = "LCPU1_leakage")
if "BCPU6_leakage" in all_df_dict:
    bcpu_6_final_df.to_excel(writer, sheet_name = "BCPU6_leakage")
if "BCPU7_leakage" in all_df_dict:
    bcpu_7_final_df.to_excel(writer, sheet_name = "BCPU7_leakage")

writer.save()


# Runtime calculation
end_time     = time.time()
duration_sec = end_time - start_time - (user_input_end_time - user_input_start_time)

if duration_sec//60 != 0:
    duration_min = duration_sec/60
    if duration_min//60 != 0:
        duration = duration_min/60
        tag      = "hr"
    else:
        duration = duration_min
        tag     = "min"
else:
    duration = duration_sec
    tag      = "sec"

print("")
print("")
print("All power data calculation completed")
print("Process took ", duration, tag, "to finish")
print("Please check outputs here: ", output_file_name)