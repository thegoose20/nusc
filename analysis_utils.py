import pandas as pd

def getColumnValuesAsLists(df, col_name):
    col_values = list(df[col_name])
    col_list_values = [value[1:-1].split(", ") for value in col_values]
    df[col_name] = col_list_values
    return df

def getColumnValuesAs2dList(df, col_name, replace=False):
    col_list = list(df[col_name])
    outer_lists = [outer_list[2:-2].split("], ") for outer_list in col_list]
    inner_lists = []
    for inner_string in outer_lists:
        # print(inner_string)
        inner_list = [token_string.strip("'[").split("', '") for token_string in inner_string]
        inner_lists.append(inner_list)
   
    if replace:
        df = df.drop(columns=[col_name])
        df.insert(len(df.columns), col_name, inner_lists)
    else:
        df.insert(len(df.columns), col_name+"_as_2d_list", inner_lists)
    
    return df