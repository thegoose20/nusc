import pandas as pd
import nltk
from nltk.text import Text

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

def makeConcordanceDF(text, word_list):
    query, right, left = [], [], []
    for word in word_list:
        c = text.concordance_list(word)
        i, maxI = 0, len(c)
        if maxI == 0:
            left += ["none"]
            right += ["none"]
            query += [word]
        while i < maxI:
            left += [" ".join(c[i].left)]
            right += [" ".join(c[i].right)]
            query += [word]
            i += 1
    return pd.DataFrame({"left": left, "query": query, "right": right})


'''
Given a list of text strings and a file path, write the text strings
to a file at the location specified in the file path.  Each text string
will be separated by one newline in the file.  If the file already exists
and the optional 'overwrite' parameter is left on, if a file already exists
at the specified location, it will be overwritten.  If the 'overwrite'
parameter is turned off (i.e., has the boolean value False), then if a 
file already exists at the specified location, the input list of text 
strings will be added to the existing contents of the file (i.e., appended
to the end of the file).
'''
def writeTxtFile(list_of_strings, filepath, overwrite=True):
    if overwrite:
        with open(filepath, "w") as f:  
            f.write("")  
            f.close()
    for s in list_of_strings:
        with open(filepath, "a") as f:
            if "\n" in s:
                s.replace("\n", "   ") # replace existing newlines with a triple space
            f.write(s)
            f.write("\n") # separate each description with a newline
    f.close()
    print("Wrote", filepath)