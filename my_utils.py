import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
import sklearn.metrics
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

'''
Given a child in an ElementTree tree, a tag name, and a list of characters to replace 
(optional; defaults are provided), create a string or list of strings, if the tag is
either 'langmaterial' or 'controlaccess', of all the text contained in the open and 
close tags for the input tag name.
'''
chars = ["\xa01953","\xa0"]
def getAllText(child, tag, chars_to_replace=chars):
    all_text = ""
    # Gather all the text under metadata field tags, including those enclosed in
    # additional tags (for example: <p> or <note> tags)
    for text_block in child.itertext():
        if len(text_block) > 0:
            text_block = text_block.strip()
            # Include a paragraph break because sequences of text strings enclosed
            # in <p> or <note> tags will otherwise have no separation between them.
            all_text = all_text + text_block + "\n"
    for char in chars_to_replace:
        if char in all_text:
            all_text = all_text.replace(char," ")
    if (tag == 'langmaterial') or (tag == 'controlaccess'):
        all_text = all_text.strip()
        final_text = all_text.split("\n\n")
    else:
        final_text = all_text.strip()  # Remove leading and trailing whitespace
    return final_text


'''
Given a URL to catalog metadata in Encoded Archival Description format (an XML format)
that is ISAD(G) 2 compliant, extract the descriptions (text) between unittitle, unitid,
unitdate, bioghist, scopecontent, processinfo, langmaterial, and controlaccess tags.
Output a list of dictionaries, where each key is a tag name and each value is the 
description associated with that tag.  Each dictionary corresponds to one fonds, or 
archival collection (the highest level of an archival hieararchy).
'''
def extractMetadata(xml_path):
    # Create an ElementTree tree and get the tree's root
    content = urllib.request.urlopen(xml_path)
    xmlTree = ET.parse(content)
    root = xmlTree.getroot()

    # Extract metadata descriptions from the below-specified fields in the tree
    metadata_field_tags = [
        "unittitle", "unitid", "unitdate", "bioghist", "scopecontent", 
        "processinfo", "langmaterial", "controlaccess"
    ]
    d_descs = {
        'unittitle': "", 'unitid': "", 'unitdate': "", 'bioghist': "", 'scopecontent': "", 
        'processinfo': "", 'langmaterial': "", 'controlaccess': ""
    }
    list_metadata = []
    for child in xmlTree.iter():
        tag = child.tag
        # Each time loop hits a <c> tag, record the metadata descriptions gathered
        # thus far and start a new d_descs dictionary
        if tag == "c":
            list_metadata += [d_descs]
            d_descs = {
                'unittitle': "", 'unitid': "", 'unitdate': "", 'bioghist': "", 'scopecontent': "", 
                'processinfo': "", 'langmaterial': "", 'controlaccess': ""
            }
        elif tag in metadata_field_tags:
            all_text = getAllText(child, tag)
            d_descs[tag] = all_text
        else:
            continue

    # If there are only top-level descriptions (fonds-level descriptions between <archdesc> tags), 
    # we'll need to add them to the metadata list here (because they won't have been added earlier 
    # because the for loop will never hit a <c> tag)
    if len(list_metadata) == 0:
        list_metadata += [d_descs]

    # Return the list of dictionaries with the extracted metadata descriptions stored as values
    # and the metadata fields (also the XML tag names) stored as keys
    return list_metadata


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
