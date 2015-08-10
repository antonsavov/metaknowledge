#Written by Reid McIlroy-Young for Dr. John McLevey, University of Waterloo 2015

import itertools
import io
import collections

from .citation import Citation
from .constants import tagNameConverter, tagsAndNames, fullToTag
from .recordTagFunctions import tagToFunc

"""
This file contains the Record class for isilib. The record class is used to represent a single records meta-data from WOS.
"""


class BadISIRecord(Warning):
    """
    Exception thrown by the record parser to indicate a mis-formated record.
    this occurs when some component of the record does not parse. It will be any  of:
        "Missing field on line (line Number):(line)", which indicates a line was to short where there should have been a tag followed by information

        "End of file reached before ER", which indicates the file end before the 'ER' indicator appeared, 'ER' indicates the end of a record. This is often due to a copy and paste error.

        "Duplicate tags in record", which indicates the record had 2 or more lines with the same tag. This is often due to a copy and paste error.

        "Missing WOS number", which indicates the record did not have a 'UT' tag. This tag allows comparison between Record objects so if missing most comparisons will fail.

    Records with a BadISIRecord error are likely incomplete or the combination of two or more single records.
    """
    pass

class BadISIFile(Warning):
    """
    Exception thrown by isiParser for mis-formated files
    """
    pass

class Record(object):
    """
    Class for full WOS records

    It is meant to be immutable, many of the methods and attributes are evaluated when first called not when the object is created an the results are stored in a private dictionary.



    It requires that the record contains a WOS number and have tags for each field.
    """
    def __init__(self, inRecord, taglist = (), sFile = '', sLine = 0):
        self._unComputedTags = set()
        self.bad = False
        self.error = None
        self.tags = taglist
        self._sourceFile = sFile
        self._sourceLine = sLine
        if isinstance(inRecord, dict):
            self._fieldDict = inRecord
        elif isinstance(inRecord, itertools.chain):
            try:
                self._fieldDict = recordParser(inRecord)
            except BadISIRecord as b:
                self.bad = True
                self.error = b
            finally:
                if hasattr(self, '_fieldDict') and 'UT' in self._fieldDict:
                    self._wosNum = self._fieldDict['UT'][0]
                else:
                    self._wosNum = None
                    self.bad = True
                    self.error = BadISIRecord("Missing WOS number")
        elif isinstance(inRecord, io.IOBase):
            try:
                self._fieldDict = recordParser(enumerate(inRecord))
            except BadISIRecord as b:
                self.bad = True
                self.error = b
                self._fieldDict = {}
            finally:
                if 'UT' in self._fieldDict:
                    self._wosNum = self._fieldDict['UT'][0]
                else:
                    self._wosNum = None
                    self.bad = True
                    self.error = BadISIRecord("Missing WOS number")
        elif isinstance(inRecord, str):
            try:
                def addChartoEnd(lst):
                    for s in lst:
                        yield s + '\n'
                self._fieldDict = recordParser(enumerate(addChartoEnd(inRecord.split('\n')), start = 1))
                #string io
            except BadISIRecord as b:
                self.bad = True
                self.error = b
                self._fieldDict = {}
            finally:
                if 'UT' in self._fieldDict:
                    self._wosNum = self._fieldDict['UT'][0]
                else:
                    self._wosNum = "NO WOS NUMBER"
                    self.bad = True
                    self.error = BadISIRecord("Missing WOS number")
        for tag in self._fieldDict:
            if tag != 'UT':
                self.__dict__[tag] = None
                self._unComputedTags.add(tag)
                try:
                    fullName = tagNameConverter[tag]
                except KeyError:
                    pass
                else:
                    self.__dict__[fullName] = None
                    self._unComputedTags.add(fullName)

    def __getattribute__(self, name):
        """
        Hack to get the attributes correct
        """
        try:
            val = object.__getattribute__(self, name)
        except AttributeError:
            if name in tagsAndNames:
                return None
            else:
                raise
        else:
            if val != None:
                return val
            else:
                if name in self._unComputedTags:
                    try:
                        otherName = tagNameConverter[name]
                    except KeyError:
                        try:
                            tagVal = tagToFunc[name](self._fieldDict[name])
                        except KeyError:
                            tagVal = self._fieldDict[name]
                        setattr(self, name, tagVal)
                        self._unComputedTags.remove(name)
                    else:
                        try:
                            prossFunc = tagToFunc[name]
                        except KeyError:
                            try:
                                prossFunc = tagToFunc[otherName]
                            except KeyError:
                                prossFunc = lambda x: x
                        try:
                            tagVal = prossFunc(self._fieldDict[name])
                        except KeyError:
                            tagVal = prossFunc(self._fieldDict[otherName])
                        object.__setattr__(self, name, tagVal)
                        object.__setattr__(self, otherName, tagVal)
                        self._unComputedTags.remove(name)
                        self._unComputedTags.remove(otherName)
                return object.__getattribute__(self, name)


    def __str__(self):
        """
        returns a string with the title of the file as given by self.title(), if there is not one it returns "Untitled record"
        """
        if self.title:
            return self.title
        else:
            return "Untitled record"

    def __eq__(self, other):
        """
        returns true if the WOS numbers of both Records are identical.
        if either is bad False is returned
        """
        if self.bad or other.bad:
            return False
        else:
            return self.wosString == other.wosString

    def __ne__(self, other):
        """
        returns the opposite of __eq__
        """
        return not self == other

    def __hash__(self):
        """
        returns a hash of the WOS number.
        If bad returns a hash of the fields, these could be blank
        bad Records are likely to cause hash collisions
        """
        if self.bad:
            return hash(str(self._fieldDict.values()) + str(self.error))
        return hash(self._wosNum)

    def __getstate__(self):
        """
        gets the __dict__ of the Record
        """
        return self.__dict__

    def __setstate__(self, state):
        """
        This is necessary because __getattribute__ is overwritten
        """
        for k in state:
            object.__setattr__(self, k, state[k])

    @property
    def wosString(self):
        """
        Returns the WOS number (UT tag) of the record
        """
        return self._wosNum

    @property
    def UT(self):
        """
        Returns the UT tag (WOS number) of the record
        """
        return self._wosNum

    def getTag(self, tag):
        """
        returns a list containing the raw data of the record associated with tag.
        Each line of the record is one string in the list.
        """
        if tag in self._fieldDict:
            return self._fieldDict[tag]
        elif tag in fullToTag and fullToTag[tag] in self._fieldDict:
            return self._fieldDict[fullToTag[tag]]
        else:
            return None

    def createCitation(self):
        """
        Creates a citation string for the Record by reading the relevant tags(year, j9, volume, beginningPage, DOI) and using it to start a Citation object
        """
        valsLst = []
        if self.authorsShort:
            valsLst.append(self.authorsShort[0].replace(',', ''))
        if getattr(self, "year", False):
            valsLst.append(str(self.year))
        if getattr(self, "j9", False):
            valsLst.append(self.j9)
        if getattr(self, "volume", False):
            valsLst.append('V' + str(self.volume))
        if getattr(self, "beginningPage", False):
            valsLst.append('P' + str(self.beginningPage))
        if getattr(self, "DOI", False):
            valsLst.append('DOI ' + self.DOI)
        return Citation(', '.join(valsLst))

    def getTagsList(self, taglst):
        """"
        returns a list of the results of getTag for each tag in taglist, it has the same order as the original.
        """
        retList = []
        for tag in taglst:
            retList.append(self.getTag(tag))
        return retList

    def getTagsDict(self, taglst):
        """"
        returns a dict of the results of getTag, with the elements of taglist as the keys and the results as the values.
        """
        retDict = {}
        for tag in taglst:
            retDict[tag] = self.getTag(tag)
        return retDict

    def activeTags(self):
        """
        Returns a list of all the tags the original isi record had
        """
        return list(self._fieldDict.keys())

    def writeRecord(self, infile):
        """
        writes to infile the original contents of the Record
        """
        if self.bad:
            raise Exception
        else:
            for tag in self._fieldDict.keys():
                for i, value in enumerate(self._fieldDict[tag]):
                    if i == 0:
                        infile.write(tag + ' ')
                    else:
                        infile.write('   ')
                    infile.write(value + '\n')
            infile.write("ER\n")

def recordParser(paper):
    """
    recordParser() reads the file paper until it reaches 'ER'.
    For each field tag it adds an entry to the returned dict with the tag as the key and a list of the entries as the value, the list has each line separately
    """
    tagList = []
    doneReading = False
    for l in paper:
        if len(l[1]) < 3:
            #Line too short
            raise BadISIRecord("Missing field on line " + str(l[0]) + " : " + l[1])
        elif 'ER' in l[1][:2]:
            #Reached the end of the record
            doneReading = True
            break
        elif l[1][2] != ' ':
            #Field tag longer than 2 or offset in some way
            raise BadISIFile("Field tag not formed correctly on line " + str(l[0]) + " : " + l[1])
        elif '   ' in l[1][:3]: #the string is three spaces in row
            #No new tag append line to current tag (last tag in tagList)
            tagList[-1][1].append(l[1][3:-1])
        else:
            #New tag create new entry at the end of tagList
            tagList.append((l[1][:2], [l[1][3:-1]]))
    if not doneReading:
        raise BadISIRecord("End of file reached before ER: " + l[1])
    else:
        retdict = collections.OrderedDict(tagList)
        if len(retdict) == len(tagList):
            return retdict
        else:
            dupSet = set()
            for tupl in tagList:
                if tupl[0] in retdict:
                    dupSet.add(tupl[0])
            raise BadISIRecord("Duplicate tags (" + ', '.join(dupSet) + ") in record")
