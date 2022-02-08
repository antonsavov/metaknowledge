import json


def isCumincadFile(infile):
    """Determines if _infile_ is the path to a Cumincad file. A file is considerd to be a Cumincad file if it is a JSON file and the JSON object has a field "source" equal to "cumincad".

    # Parameters

    _infile_ : `str`

    > The path to the targets file

    # Returns

    `bool`

    > `True` if the file is a cumincad file
    """
    try:
        with open('cumincaddata.json', 'r', encoding = 'utf-8') as openfile:
            json_object = json.load(openfile)
        if json_object['source'] == 'cumincad':
            return True
        else:
            return False
    except (StopIteration, UnicodeDecodeError, json.JSONDecodeError, KeyError):
        return False
    else:
        return False

def cumincadParser(cumincadFile):
    """Parses a scopus file, _scopusFile_, to extract the individual lines as [ScopusRecords](../classes/ScopusRecord.html#metaknowledge.scopus.ScopusRecord).

    A Scopus file is a csv (Comma-separated values) with a complete header, see [`scopus.scopusHeader`](#metaknowledge.scopus) for the entries, and each line after it containing a record's entry. The string valued entries are quoted with double quotes which means double quotes inside them can cause issues, see [scopusRecordParser()](#metaknowledge.scopus.recordScopus.scopusRecordParser) for more information.

    # Parameters

    _cumincadFile_ : `str`

    > A path to a valid cumincad file, use [isScopusFile()](#metaknowledge.scopus.scopusHandlers.isScopusFile) to verify

    # Returns

    `set[cumincadRecord]`

    > Records for each of the entries
    """
    #assumes the file is Scopus
    recSet = set()
    error = None
    lineNum = 0
    try:
        with open(cumincadFile, 'r', encoding = 'utf-8') as openfile:
            #read the file
            json_object = json.load(openfile)
            for record in json_object['records']:
                try:                
                    recSet.add(CumincadRecord(row, header = header, sFile = cumincadFile, sLine = line))
                except BadScopusFile as e:
                    if error is None:
                        error = BadCumincadFile("The file '{}' is unparsable".format(cumincadFile))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
        if error is None:
            error = BadCumincadFile("The file '{}' has parts of it that are unparsable".format(cumincadFile))
    return recSet, error