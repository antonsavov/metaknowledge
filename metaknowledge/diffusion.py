"""
"""
from .constants import tagsAndNames
from .graphHelpers import _ProgressBar
from .recordCollection import RecordCollection

import networkx as nx
import metaknowledge

def diffusionGraph(source, target, sourceType = "raw", targetType = "raw"):
    """Takes in two [`RecordCollections`](#RecordCollection.RecordCollection) and produces a graph of the citations of the `Records` of _source_ by the `Records` of _target_. By default the graph is of `Record` objects but this can be changed with the _sourceType_ and _targetType_ keywords.

    Each node on the graph has two boolean attributes, `"source"` and `"target"` indicating if they are targets or sources. Note, if the types of the sources and targets are different the attributes will not be checked for overlap of the other type. e.g. if the source type is `'TI'` (title) and the target type is `'UT'` (WOS number), and there is some overlap of the targets and sources. Then the Record corresponding to a source node will not be checked for being one of the titles of the targets, only its WOS number will be considered.

    # Parameters

    _source_ : `RecordCollection`

    >A metaknowledge `RecordCollection` containing the `Records` being cited

    _target_ : `RecordCollection`

    >A metaknowledge `RecordCollection` containing the `Records` citing those in _source_

    _sourceType_ : `str`

    >default `'raw'`, if `'raw'` the returned graph will contain `Records` as source nodes. If it is a WOS tag of the long name of one then the nodes will be of that type.

    _targetType_ : `str`

    >default `'raw'`, if `'raw'` the returned graph will contain `Records` as target nodes. If it is a WOS tag of the long name of one then the nodes will be of that type.

    # Returns

    `networkx Directed Graph`

    >A directed graph of the diffusion network
    """
    if sourceType != "raw" and sourceType not in tagsAndNames:
        raise RuntimeError("{} is not a valid node type, only 'raw' or those strings in tagsAndNames are allowed".format(nodeType))
    if targetType != "raw" and targetType not in tagsAndNames:
        raise RuntimeError("{} is not a valid node type, only 'raw' or those strings in tagsAndNames are allowed".format(nodeType))
    if metaknowledge.VERBOSE_MODE:
        PBar = _ProgressBar(0, "Starting to make a diffusion network")
        count = 0
        maxCount = len(source)
    else:
        PBar = None
    sourceDict = {}
    workingGraph = nx.DiGraph()
    for Rs in source:
        if PBar:
            count += 1
            PBar.updateVal(count / maxCount * .25, "Analyzing source: " + str(Rs))
        RsVal, RsExtras = makeNodeID(Rs, sourceType)
        if RsVal:
            sourceDict[Rs.createCitation()] = RsVal
            for val in RsVal:
                if val not in workingGraph:
                    workingGraph.add_node(val, source = True, target = False, **RsExtras)
    if PBar:
        count = 0
        maxCount = len(target)
        PBar.updateVal(.25, "Done analyzing sources, starting on targets")
    for Rt in target:
        RtVal, RtExtras = makeNodeID(Rt, targetType)
        if PBar:
            count += 1
            PBar.updateVal(count / maxCount * .75 + .25, "Analyzing target: " + str(Rt))
        if RtVal:
            for val in RtVal:
                if val not in workingGraph:
                    workingGraph.add_node(val, source = False, target = True, **RtExtras)
                else:
                    workingGraph.node[val]["target"] = True
                targetCites = Rt.CR
                if targetCites:
                    for Rs in (sourceDict[c] for c in targetCites if c in sourceDict):
                        for sVal in Rs:
                            workingGraph.add_edge(val, sVal)
    if PBar:
        PBar.finish("Done making a diffusion network of {} sources and {} targets".format(len(source), len(target)))
    return workingGraph


def diffusionCount(source, target, sourceType = "raw", pandasFriendly = False):
    """Takes in two [`RecordCollections`](#RecordCollection.RecordCollection) and produces a `dict` counting the citations of the `Records` of _source_ by the `Records` of _target_. By default the `dict` uses `Record` objects as keys but this can be changed with the _sourceType_ keyword to any of the WOS tags.

    # Parameters

    _source_ : `RecordCollection`

    >A metaknowledge `RecordCollection` containing the `Records` being cited

    _target_ : `RecordCollection`

    >A metaknowledge `RecordCollection` containing the `Records` citing those in _source_

    _sourceType_ : `optional [str]`

    >default `'raw'`, if `'raw'` the returned `dict` will contain `Records` as keys. If it is a WOS tag of the long name of one then the keys will be of that type.

    _pandasFriendly_ : `optional [bool]`

    > default `False`, makes the output be a dict with two keys one `"Record"` is the list of Records ( or data type requested by _sourceType_) the other is their occurence counts as `"Counts"`.

    # Returns

    `dict[:int]`

    >A dictionary with the type given by _sourceType_ as keys and integers as values.
    """
    if sourceType != "raw" and sourceType not in tagsAndNames:
        raise RuntimeError("{} is not a valid node type, only 'raw' or those strings in tagsAndNames are allowed".format(nodeType))
    if not isinstance(source, RecordCollection) or not isinstance(target, RecordCollection):
        raise RuntimeError("Source and target must be RecordCollections.")
    if metaknowledge.VERBOSE_MODE:
        PBar = _ProgressBar(0, "Starting to analyse a diffusion network")
        count = 0
        maxCount = len(source)
    else:
        PBar = None
    if PBar:
        count = 0
        maxCount = len(source)
        PBar.updateVal(.25, "Done analyzing sources, starting on targets")
    sourceDict = {}
    sourceSet = set()
    for Rs in source:
        if PBar:
            count += 1
            PBar.updateVal(count / maxCount * .25, "Analyzing source: " + str(Rs))
        RsVal, RsExtras = makeNodeID(Rs, sourceType)
        if RsVal:
            sourceDict[Rs.createCitation()] = RsVal
            sourceSet.update(RsVal)
    sourceCounts = {s : 0 for s in sourceSet}
    if PBar:
        count = 0
        maxCount = len(target)
        PBar.updateVal(.25, "Done analyzing sources, starting on targets")
    for Rt in target:
        if PBar:
            count += 1
            PBar.updateVal(count / maxCount * .75 + .25, "Analyzing target: " + str(Rt))
        targetCites = Rt.CR
        if targetCites:
            for Rs in (sourceDict[c] for c in targetCites if c in sourceDict):
                for sVal in Rs:
                    sourceCounts[sVal] += 1
    if PBar:
        PBar.finish("Done making a diffusion network of {} sources and {} targets".format(len(source), len(target)))
    if pandasFriendly:
        countLst = []
        recLst = []
        for rec, occ in sourceCounts.items():
            countLst.append(occ)
            recLst.append(rec)
        retDict = {"Record" : recLst, "Count" : countLst}
        return retDict
    else:
        return sourceCounts

def makeNodeID(Rec, ndType, extras = None):
    """Helper to make a node ID, extras is currently not used"""
    if ndType == 'raw':
        recID = Rec
    else:
        recID =  getattr(Rec, ndType)
    if recID is None:
        pass
    elif isinstance(recID, list):
        recID = tuple(recID)
    else:
        recID = (recID, )
    extraDict = {}
    if extras:
        for tag in extras:
            if tag == "raw":
                extraDict[Tag] = Rec
            else:
                extraDict[Tag] = getattr(Rec, tag)
    return recID, extraDict
