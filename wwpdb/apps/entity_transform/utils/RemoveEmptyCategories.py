##
# File:  RemoveEmptyCategories.py
# Date:  28-Apr-2013
# Updates:
##
"""
Remove empty categories in cif file

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2012 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import traceback
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter
from mmcif.api.PdbxContainers import DataContainer
#


def ReadCif(filepath):
    try:
        myDataList = []
        ifh = open(filepath, 'r')
        pRd = PdbxReader(ifh)
        pRd.read(myDataList)
        ifh.close()
        return myDataList[0]
    except:  # noqa: E722 pylint: disable=bare-except
        traceback.print_exc(file=sys.stderr)
        return None
    #
#


def WriteCif(myBlock, filepath):
    try:
        myDataList = []
        ofh = open(filepath, 'w')
        myDataList.append(myBlock)
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(myDataList)
        ofh.close()
    except:  # noqa: E722 pylint: disable=bare-except
        traceback.print_exc(file=sys.stderr)
        sys.exit(0)
    #
#


def RemoveEmptyCategories(filepath):
    myBlock = ReadCif(filepath)
    blockName = myBlock.getName()
    newBlock = DataContainer(blockName)
    #
    catList = myBlock.getObjNameList()
    for catName in catList:
        myCat = myBlock.getObj(catName)
        row = myCat.getRowCount()
        if row > 1:
            newBlock.append(myCat)
            continue
        #
        has_value = False
        attributeList = myCat.getAttributeList()
        for attr in attributeList:
            val = myCat.getValue(attr, 0)
            if val != '?' and val != '.':
                has_value = True
                break
            #
        #
        if has_value:
            newBlock.append(myCat)
        #
    #
    WriteCif(newBlock, filepath)
#
