##
# File:  MergePolymer.py
# Date:  04-Dec-2012
# Updates:
##
"""
Merge polymer(s) in coordinate cif file.

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


class MergePolymer(UpdateBase):
    """ Class responsible for merging polymer(s) in coordinate cif file.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(MergePolymer, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)

    def updateFile(self):
        """ Update coordinate cif file
        """
        options = self._getMergeOptions()
        if options:
            self._runUpdateScript('MergePolymer', 'Merge to polymer', 'run-merge', options)
        #
