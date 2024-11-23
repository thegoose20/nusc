import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd

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