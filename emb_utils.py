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