##
# File:  SplitPolymer.py
# Date:  12-Dec-2012
# Updates:
##
"""
Split polymer(s) in coordinate cif file.

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

from wwpdb.apps.entity_transform.update.UpdateBase import UpdateBase


class SplitPolymer(UpdateBase):
    """ Class responsible for spliting polymer(s) in coordinate cif file.

    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(SplitPolymer, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)

    def updateFile(self):
        """ Update coordinate cif file
        """
        options = self.__getUsrDefinedOptions()
        if self._message:
            return
        #
        self._runUpdateScript('SplitPolymer', 'Split polymer to polymer(s)/non-polymer(s)', 'run-split', options)

    def __getUsrDefinedOptions(self):
        """ get user defined options
        """
        entityList = self._reqObj.getValueList('entity')
        if not entityList:
            self._message += 'No entity found. <br/>\n'
            return
        #
        options = ''
        for val in entityList:
            entity = str(val)
            chainList = self._reqObj.getValue('chain_' + entity)
            if not chainList:
                self._message += 'No PDB chain ID(s) found for entity ' + entity + '. <br/>\n'
                continue
            #
            splitList = self._reqObj.getValueList('split_' + entity)
            if not splitList:
                self._message += 'No split position(s) found for entity ' + entity + '. <br/>\n'
                continue
            #
            splits = str(','.join(splitList))
            #
            clist = chainList.split(',')
            for chain_id in clist:
                options += ' -split ' + str(chain_id) + ':' + splits
            #
        #
        return options
