import pandas as pd
import numpy as np
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
import sklearn.metrics
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

'''
Given a DataFrame, create a new DataFrame with a subset of the data 
in new columns, where all text to be classified from the original DataFrame
is combined into a single column in the new DataFrame.
Input: a DataFrame, a list of the names of columns in that DataFrame 
with text that should be put into a single column, and the name (as a string)
of the column with the unique identifiers for each row in the DataFrame.
Output: a DataFrame with four columns, "eadid," "rowid," "field" (for the 
name of the metadata field from with a row's text was extracted), and "doc" 
(for the extracted text).  Any empty (NaN) "doc" rows are removed before the 
final DataFrame is returned.
'''
def transformForClassification(df, text_cols, rowid):
    unique_eadids = list(df["eadid"].unique())
    eadid_col, rowid_col, doc_col, field_col = [], [], [], []
    for eadid in unique_eadids:
        subdf = df.loc[df["eadid"] == eadid]
        for text_col in text_cols:
            docs = list(subdf[text_col])
            doc_eadids = [eadid]*len(docs)
            rowids = list(subdf[rowid])
            fields = [text_col]*len(docs)
            assert len(docs) == len(rowids)
            assert len(fields) == len(rowids)
            assert len(docs) == len(fields)
            eadid_col += doc_eadids
            doc_col += docs
            rowid_col += rowids
            field_col += fields
            
    doc_df = pd.DataFrame({
        "eadid":eadid_col, "rowid":rowid_col, "field":field_col, "doc":doc_col
        })

    # Remove any rows with an empty (NaN) doc (description)
    doc_df = doc_df[~doc_df["doc"].isna()]
    
    return doc_df


'''
Prepare the data for token classification
- Function inputs: a pandas DataFrame, the column name(s) with text for 
classification (as a list of strings), and name of the column with the rows' 
unique identifiers (default provided).  If more than one column name is input, those columns' 
text will be joined to create a new column named text.
- Function output: a pandas DataFrame with one row per token and columns for
row unique identifiers, tokens, and token unique identifiers.
'''
def getTokenDF(df, cols, row_id="description_id"):
    df = df.fillna("") # Replace NaN (empty) values with an empty string
    if len(cols) > 1:
        col_name = "text"
        df[col_name] = df[cols].apply(lambda row: (". ".join(row.values.astype(str))).lstrip(". "), axis=1)
    elif len(cols) == 1:
        col_name = cols[0]
    else: 
        return "Please provide a list of text column names containing at least one column."

    non_empty_df = df.loc[df[col_name] != ""]
    incl_row_ids = list(non_empty_df[row_id])
    
    text = list(non_empty_df[col_name])
    token_col = []
    token_id_col = []
    last_id = 0
    for row in text:
        tokens = word_tokenize(str(row))
        token_ids = list(range(last_id, len(tokens)+last_id))
        last_id = last_id+len(tokens)
        token_id_col += [token_ids]
        token_col += [tokens]
    new_df = pd.DataFrame({"description_id": incl_row_ids, "token_id": token_id_col, "token": token_col})
    new_df = new_df.explode(["token_id", "token"])

    return new_df

'''
Get features for the multilabel token classifier given an input DataFrame with one 
token per row and an embedding model and, optionally, feature columns (the defaults 
are 'token_id' and 'token').
Output a feature matrix as a numpy array.
'''
def getFeatures(df, embedding_model, feature_cols=["token_id", "token"]):
    # Zip the features
    feature_data = list(zip(df[feature_cols[0]], df[feature_cols[1]]))
    
    # Make FastText feature matrix
    feature_list = [embedding_model.wv[token.lower()] for token_id,token in feature_data]
    return np.array(feature_list)


'''
Implode a DataFrame (opposite of df.explode()).
- Function inputs: a DataFrame and a non-empty list of columns by which to group the
rest of the data.
- Function output: a DataFrame where the values in all columns except those included as 
function inputs are aggregated as a list per row (so a cell may have repeated values).
'''
def implodeDataFrame(df, cols_to_groupby):
    cols_to_agg = list(df.columns)
    for col in cols_to_groupby:
        cols_to_agg.remove(col)
    agg_dict = dict.fromkeys(cols_to_agg, lambda x: x.tolist())
    return df.groupby(cols_to_groupby).agg(agg_dict).reset_index().set_index(cols_to_groupby)


'''
Implode a DataFrame (opposite of df.explode()).
- Function inputs: a DataFrame and a non-empty list of columns by which to group the
rest of the data.
- Function output: a DataFrame where the values in all columns except those included as 
function inputs are aggregated as a set per row (so there are NO repeated values in a cell).
'''
def implodeDataFrameUnique(df, cols_to_groupby):
    cols_to_agg = list(df.columns)
    for col in cols_to_groupby:
        cols_to_agg.remove(col)
    agg_dict = dict.fromkeys(cols_to_agg, lambda x: list(set(x)))
    return df.groupby(cols_to_groupby).agg(agg_dict).reset_index().set_index(cols_to_groupby)


'''
Calculate precision, recall, and F1 score based on the input
true positive count, false positive count, and false negative count.
'''
def precisionRecallF1(tp_count, fp_count, fn_count):
    # Precision Score: ability of classifier not to label a sample that should be negative as positive; best possible = 1, worst possible = 0
    if tp_count+fp_count == 0:
        precision = 0
    else:
        precision = (tp_count/(tp_count+fp_count))
    # Recall Score: ability of classifier to find all positive samples; best possible = 1, worst possible = 0
    if tp_count+fn_count == 0:
        recall = 0
    else:
        recall = (tp_count/(tp_count+fn_count))
    # F1 Score: harmonic mean of precision and recall; best possible = 1, worst possible = 0
    if (precision+recall == 0):
        f_1 = 0
    else:
        f_1 = (2*precision*recall)/(precision+recall)
    return precision, recall, f_1