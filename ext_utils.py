# Functions for Data Extraction

import xml.etree.ElementTree as ET
from lxml import etree
import urllib.request
import pandas as pd
import numpy as np


'''
Create an ElementTree from a URL and return the tree.
'''
def getTreeFromUrl(url):
    content = urllib.request.urlopen(url)
    parser = etree.XMLParser(recover=True)  # Use recover to try to fix broken XML
    tree = etree.parse(content, parser)
    return tree


'''
Given an OAI URL, iteratively extract the text and URLs stored in the 
input tag and return a DataFrame with one column for the text and one
for the URLs.
'''
def getTextFromTag(more, catalog_url, id_tag): 
    resumptionToken = ""
    urls, eadids = [], []
    tree = getTreeFromUrl(catalog_url)
    for child in tree.iter():
        if child.tag == id_tag:
            if "https://" in child.text:
                urls += [child.text]
            else:
                eadids += [child.text]
        elif "resumptionToken" in child.tag:
            resumptionToken = child.text

    if len(resumptionToken) == 0:
        more = False
    else:
        i = 1

    while more:
        catalog_url_with_token = catalog_url + "&resumptionToken=" + resumptionToken
        resumptionToken = ""
        tree = getTreeFromUrl(catalog_url_with_token)
        for child in tree.iter():
            if child.tag == id_tag:
                if "https://" in child.text:
                    urls += [child.text]
                else:
                    eadids += [child.text]
            elif "resumptionToken" in child.tag:
                resumptionToken = child.text
            else:
                continue

        if len(resumptionToken) == 0:
            more = False
        else:
            i += 1

    print(str(i) + " resumption tokens")
    return pd.DataFrame({"eadid":eadids, "url":urls})


'''
Given a child in an ElementTree tree, a tag name, and a list of characters to replace 
(optional; defaults are provided), create a string or, if the tag is either  
'langmaterial' or 'controlaccess', list of strings, of all the text contained in the
open and close tags for the input tag name.
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
# Define tags to extract metadata from by default
tags = [
        "eadid", "unittitle", "unitid", "unitdate", "bioghist", 
        "scopecontent", "processinfo", "langmaterial", "controlaccess"
    ]

def extractMetadata(xml_path, metadata_field_tags=tags):
    # Create an ElementTree tree and get the tree's root
    content = urllib.request.urlopen(xml_path)
    xmlTree = ET.parse(content)

    # Extract metadata descriptions from the input metadata fields
    # (meaning extract the text between XML tags with the input names)
    d_descs = dict.fromkeys(metadata_field_tags, "")
    list_metadata = []
    for child in xmlTree.iter():
        tag = child.tag
        # Each time loop hits a <c> tag, record the metadata descriptions gathered
        # thus far and start a new d_descs dictionary
        if tag == "c":
            list_metadata += [d_descs]
            d_descs = dict.fromkeys(metadata_field_tags, "")
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
in new columns, where all text to be classified, or otherwise analyzed,
from the original DataFrame is combined into a single column in the new
DataFrame.
Input: a DataFrame, a list of the names of columns in that DataFrame 
with text that should be put into a single column, and the name (as a string)
of the column with the unique identifiers for each row in the DataFrame.
Output: a DataFrame with four columns, "eadid," "rowid," "field" (for the 
name of the metadata field from with a row's text was extracted), and "doc" 
(for the extracted text).  Any empty (NaN) "doc" rows are removed before the 
final DataFrame is returned.
'''
def consolidateText(df, text_cols, rowid):
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
Input:  part of or the entirety of a tag name below which you want to get text 
Output: a list of text between tags contained within the input tag_name, 
        with one list element per tagName instance
'''
def getTextBeneathTag(root, tag_name):
    text_list = []
    for child in root.iter():
        tag = child.tag
        if tag_name in tag:
            text_elem = ""
            for subchild_text in child.itertext():
                text_elem = text_elem + subchild_text
            text_list.append(text_elem)
    return text_list


'''
Input:  binary value, url for harvesting metadata, starting prefix for the end of the url, 
        and lists of metadata fields to gather
Output: lists of strings of the gathered metadata fields' descriptions, with one string 
        per fonds, series, and item in the catalog
'''
def getDescriptiveMetadata(more, archiveMetadataUrlShort, startingPrefix, ut, ui, sc, bh, pi):    #eadid
    print("Extracting descriptive metadata from", archiveMetadataUrlShort)

    archiveMetadataUrlWithPrefix = archiveMetadataUrlShort + startingPrefix
    root = getTreeFromUrl(archiveMetadataUrlWithPrefix).getroot()
    # eadid.append(getTextBeneathTag(root, "eadid"))
    ut.append(getTextBeneathTag(root, "unittitle"))
    ui.append(getTextBeneathTag(root, "unitid"))
    sc.append(getTextBeneathTag(root, "scopecontent"))
    bh.append(getTextBeneathTag(root, "bioghist"))
    pi.append(getTextBeneathTag(root, "processinfo"))
    resumptionToken = getTextBeneathTag(root, "resumptionToken")

    if len(resumptionToken) == 0:
        more = False
    else:
        i = 1

    while more:
        print("Continuing to extract...")
        archiveMetadataUrlWithToken = archiveMetadataUrlShort + "resumptionToken=" + resumptionToken[0]
        root = getTreeFromUrl(archiveMetadataUrlWithToken).getroot()
        # eadid.append(getTextBeneathTag(root, "eadid"))
        ut.append(getTextBeneathTag(root, "unittitle"))
        ui.append(getTextBeneathTag(root, "unitid"))
        sc.append(getTextBeneathTag(root, "scopecontent"))
        bh.append(getTextBeneathTag(root, "bioghist"))
        pi.append(getTextBeneathTag(root, "processinfo"))
        resumptionToken = getTextBeneathTag(root, "resumptionToken")
        if len(resumptionToken) == 0:
            more = False
        else:
            i += 1
        
        if (len(ut)) >= 37000: #>= 99000
            more = False
            print("Stopping extraction at similar number of descriptions as available in Newcastle's archival catalog.")
            # return ut, ui, sc, bh, pi

    print("Extraction complete after", str(i) + " resumption tokens!")
    return ut, ui, sc, bh, pi #eadid, 