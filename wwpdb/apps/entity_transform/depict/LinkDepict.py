##
# File:  LinkDepict.py
# Date:  10-Dec-2012
# Updates:
##
"""
Create HTML depiction for Links

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

from wwpdb.apps.entity_transform.depict.DepictBase import DepictBase
from wwpdb.apps.entity_transform.utils.LinkUtil import LinkUtil
#


class LinkDepict(DepictBase):
    """ Class responsible for generating HTML depiction of Links.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(LinkDepict, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__labelId = ''
        self.__tableData = ''
        #
        self.__links = {}
        self.__readLinkData()
        #
        self.__process()

    def getLabelId(self):
        return self.__labelId

    def getTableData(self):
        return self.__tableData

    def __readLinkData(self):
        linkutil = LinkUtil(cifObj=self._cifObj, verbose=self._verbose, log=self._lfh)
        self.__links = linkutil.getLinks()

    def __process(self):
        id = str(self._reqObj.getValue('id'))  # pylint: disable=redefined-builtin
        list = id.split(',')  # pylint: disable=redefined-builtin
        if len(list) == 1:
            list1 = list[0].split('_')
            if len(list1) == 1:
                self.__labelId = 'Chain ' + list[0]
            else:
                self.__labelId = 'Residue ' + ' '.join(list1)
        else:
            self.__labelId = 'GROUP_' + list[0]
            id = ','.join(list[1:])
        #
        if id not in self.__links:
            return
        #
        for list in self.__links[id]:
            self.__tableData += '<tr>\n'
            self.__tableData += '<td> ' + list[1] + ' </td>\n'
            self.__tableData += '<td> ' + list[0] + ' </td>\n'
            self.__tableData += '<td> ' + list[2] + ' </td>\n'
            self.__tableData += '<td> ' + list[3] + ' </td>\n'
            self.__tableData += '<td> ' + list[4] + ' </td>\n'
            self.__tableData += '<td> ' + list[5] + ' </td>\n'
            self.__tableData += '<td> ' + list[7] + ' </td>\n'
            self.__tableData += '<td> ' + list[6] + ' </td>\n'
            self.__tableData += '<td> ' + list[8] + ' </td>\n'
            self.__tableData += '<td> ' + list[9] + ' </td>\n'
            self.__tableData += '<td> ' + list[10] + ' </td>\n'
            self.__tableData += '<td> ' + list[11] + ' </td>\n'
            self.__tableData += '</tr>\n'
        #
