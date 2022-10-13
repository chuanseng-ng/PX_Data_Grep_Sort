from cal_px_power.define.cal_functions import replace_nan_with_zero, remove_row_col, df_gen_full
import pandas as pd
import sys
import time

def cal_px_power(input_file_name, output_file_name):
    # Read in excel file details into dataframes
    all_df_dict = pd.read_excel(input_file_name, sheet_name=None, engine='openpyxl')
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
    
    # Extract power_rail info from dataframe
    power_rail_list = []
    for item in top_only_df.iloc[0,:]:
        if not pd.isna(item):
            power_rail_list.append(item)

    power_rail_list.pop(0)
    power_rail_list.pop(0)

    # Show user available power_rail to choose from based on input xlsx file
    print("Here are the available power rails to choose from:")
    for count in range(len(power_rail_list)):
        print(count, "- ", power_rail_list[count])

    print("")
    print("Please input the selection numbers for each calculation")
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
        sel_input     = input("Please provide the selection numbers: ")

        if sel_input and sel_input.split:
            sel_input_split = sel_input.strip().split(" ")
            for item in sel_input_split:
                if any(item in sorted_item for sorted_item in sel_list):
                    print("An input selection has been repeated -> ", item)
                    print("Please only choose each input selection once")
                    sys.exit(1)
                elif int(item) > int(max_power_rail_count - 1):
                    print("Highest input selection number is ", max_power_rail_count - 1)
                    print("Current input selection number of ", item, " exceeds that")
                    print("Please choose within input selection range")
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
    
    # Write into excel file
    writer = pd.ExcelWriter(output_file_name, engine='xlsxwriter')
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

    return user_input_end_time - user_input_start_time