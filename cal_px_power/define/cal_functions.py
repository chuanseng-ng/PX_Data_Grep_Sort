import pandas as pd
import numpy as np

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
        curr_sel_name       = ""
        curr_sel_index_list = []

        ### Generate new block header based on combination of user-selected power rails
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