##
# File:  UpdateFile.py
# Date:  16-Oct-2012
# Updates:
##
"""
Update coordinate cif file.

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

import os
import sys

from wwpdb.apps.entity_transform.update.UpdateBase import UpdateBase
from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from wwpdb.apps.entity_transform.utils.CompUtil import CompUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage
#


class UpdateFile(UpdateBase):
    """ Class responsible for Update coordinate cif file.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(UpdateFile, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__selectedInstIds = []

    def updateFile(self):
        """ Update coordinate cif file
        """
        self.__getSelectedInstIds()
        options = self.__getOptions()
        if self._message:
            return
        #
        self._runUpdateScript('UpdateEntry', 'Update Entry', 'update-entry', options)

    def __getSelectedInstIds(self):
        """ Get selected instance IDs
        """
        count = int(str(self._reqObj.getValue('count')))
        for i in range(0, count):
            id = self._reqObj.getValue('id_' + str(i))  # pylint: disable=redefined-builtin
            if not id:
                continue
            #
            ilist = id.split(',')
            dic = {}
            dic['instid'] = ilist[0]
            if len(ilist) == 2:
                dic['only'] = ilist[1]
            #
            has_value = False
            match_id = self._reqObj.getValue('match_id_' + str(i))
            if match_id:
                mlist = match_id.split(',')
                dic['hitid'] = mlist[1]
                dic['fileid'] = mlist[1]
                has_value = True
            #
            user_defined_id = self._reqObj.getValue('user_defined_id_' + str(i))
            if user_defined_id:
                dic['inputid'] = user_defined_id.upper()
                has_value = True
            #
            if has_value:
                self.__selectedInstIds.append(dic)
            #
        #

    def __getOptions(self):
        """ Get options from user selection
        """
        optionlist = ''
        if not self.__selectedInstIds:
            self._message = '<pre>\nNothing selected.\n</pre>\n'
            return optionlist
        #
        extraOption = str(self._reqObj.getValue('option'))
        if extraOption:
            optionlist += extraOption
        #
        error = ''
        for dic in self.__selectedInstIds:
            error1 = self.__runGraphMatch(dic)
            if error1:
                error += error1
                continue
            #
            if 'fileid' not in dic:
                error += dic['instid'] + ' has no match.\n'
                continue
            #
            mapfile = os.path.join(self._sessionPath, 'search', dic['instid'], dic['instid'] + '_' + dic['fileid'] + '.cif')
            if not os.access(mapfile, os.F_OK):
                error += dic['instid'] + ' has no match file.\n'
                continue
            #
            if 'only' in dic:
                mapfile += ':metadataonly'
            optionlist += ' -mapping ' + mapfile
        #
        optionlist += ' '
        if error:
            self._message = '<pre>\n' + error + '\n</pre>\n'
        #
        return optionlist

    def __runGraphMatch(self, dic):
        """ Run Graph match and get mapping file
        """
        if 'inputid' not in dic:
            return ''
        #
        compObj = CompUtil(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        error = compObj.checkInputId(dic['inputid'])
        if error:
            return error
        #
        templateFile = compObj.getTemplateFile(dic['inputid'])
        if not templateFile:
            return 'Can not find chemical component file for ID ' + dic['inputid'] + '\n'
        #
        instancePath = os.path.join(self._sessionPath, 'search', dic['instid'])
        option = ' -template ' + templateFile + ' -cif ' + os.path.join(instancePath, dic['instid'] + '.orig.cif') \
            + ' -path ' + os.path.join(self._sessionPath, 'search') + ' -idlist ' + dic['instid'] + ' '
        #
        if dic['inputid'][:4] == 'PRD_':
            option += ' -prd_id ' + dic['inputid'] + ' '
        #
        if not self._cmdUtil:
            self._cmdUtil = CommandUtil(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        self._cmdUtil.setSessionPath(instancePath)
        self._cmdUtil.runAnnotCmd('MatchInstanceWithTemplate', '', '', 'run-match.log', 'run-match.clog', option)
        error = GetLogMessage(os.path.join(instancePath, 'run-match.log'))
        if error:
            return error
        #
        dic['hitid'] = dic['inputid']
        dic['fileid'] = 'TEMP'
        return ''
