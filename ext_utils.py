# Functions for Data Extraction

import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd
import numpy as np

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
        "unittitle", "unitid", "unitdate", "bioghist", "scopecontent", 
        "processinfo", "langmaterial", "controlaccess"
    ]

def extractMetadata(xml_path, metadata_field_tags=tags):
    # Create an ElementTree tree and get the tree's root
    content = urllib.request.urlopen(xml_path)
    xmlTree = ET.parse(content)
    root = xmlTree.getroot()

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


