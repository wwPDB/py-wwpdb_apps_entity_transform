##
# File:  UpdateBase.py
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

import os
import sys
import inspect

from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from wwpdb.apps.entity_transform.utils.GetLogMessage import GetLogMessage


class UpdateBase(object):
    """ Class responsible for merging polymer(s) in coordinate cif file.

    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        self._verbose = verbose
        self._lfh = log
        self._reqObj = reqObj
        self._cifObj = summaryCifObj
        self._sObj = None
        self._sessionPath = None
        self._cmdUtil = None
        #
        self._identifier = str(self._reqObj.getValue("identifier"))
        self._modelCIFile = self._identifier + '_model_P1.cif'
        #
        self._message = ''
        self.__groups = []
        #
        self.__getSession()

    def getMessage(self):
        """ Return result message
        """
        return self._message

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self._sObj = self._reqObj.newSessionObj()
        self._sessionPath = self._sObj.getPath()
        if self._verbose:
            self._lfh.write("------------------------------------------------------\n")
            self._lfh.write("+%s.%s() - creating/joining session %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self._sObj.getId()))
            self._lfh.write("+%s.%s() - session path %s\n" % (self.__class__.__name__, inspect.currentframe().f_code.co_name, self._sessionPath))
        #

    def _getMergeOptions(self, ligandFlag=False):
        """ Get merge options
        """
        self.__getGroups(ligandFlag)
        if self._message or (not self.__groups):
            return ''
        #
        options = ''
        for group in self.__groups:
            options += ' -group ' + ','.join(group) + ' '
        #
        return options

    def _runUpdateScript(self, progName, taskName, logRootName, options):
        """ Run update program
        """
        if not os.access(os.path.join(self._sessionPath, self._modelCIFile), os.F_OK):
            self._message = 'Model coordinate file ' + self._modelCIFile + ' does not exist.'
            return
        #
        if not self._cmdUtil:
            self._cmdUtil = CommandUtil(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        #
        self._cmdUtil.setSessionPath(self._sessionPath)
        self._cmdUtil.runAnnotCmd(progName, self._modelCIFile, self._modelCIFile, logRootName + '.log', logRootName + '.clog', options)
        #
        logfile = os.path.join(self._sessionPath, logRootName + '.log')
        if not os.access(logfile, os.F_OK):
            self._message = 'Option "' + taskName + '" failed. No log file found.'
            return
        #
        error = GetLogMessage(logfile)
        if error:
            self._message = '<pre>\n' + error + '</pre>\n'
        elif self._cifObj:
            self._message = 'Entry ' + self._cifObj.getEntryIds() + ' updated.'
        else:
            self._message = 'Entry updated.'
        #

    def __getGroups(self, ligandFlag):
        """ Get groups
        """
        order_dic = {}
        group_dic = {}
        self.__processList('chain', order_dic, group_dic)
        self.__processList('ligand', order_dic, group_dic)
        #
        multiGroupFlag = False
        if len(group_dic) > 1:
            multiGroupFlag = True
        #
        for id, list in group_dic.items():  # pylint: disable=redefined-builtin
            # num = len(list)
            int_order_dic = {}
            for v in list:
                if v not in order_dic:
                    continue
                #
                order = int(order_dic[v])
                if order in int_order_dic:
                    int_order_dic[order].append(v)
                else:
                    int_order_dic[order] = [v]
                #
            #
            # Check unique order numbering
            #
            foundError = False
            order_list = []
            for k, list2 in int_order_dic.items():
                order_list.append(k)
                if len(list2) <= 1:
                    continue
                #
                text = ''
                for v in list2:
                    list3 = v.split('_')
                    if text:
                        text += ', '
                        if len(list3) > 1:
                            text += 'ligand ' + v
                        else:
                            text += 'chain ' + v
                        #
                    else:
                        if len(list3) > 1:
                            text += 'Ligand ' + v
                        else:
                            text += 'Chain ' + v
                        #
                    #
                #
                self._message += text + ' have same order number "' + str(k) + '". <br/>\n'
                foundError = True
            #
            # Check missing order numbering
            #
            for i in range(0, len(list)):
                j = i + 1
                if j in int_order_dic:
                    continue
                #
                if multiGroupFlag:
                    self._message += 'In group "' + id + '", order number "' + str(j) + '" is missing. <br/>\n'
                else:
                    self._message += 'Order number "' + str(j) + '" is missing. <br/>\n'
                #
                foundError = True
            #
            if foundError:
                continue
            #
            # Reorder group based on order number
            #
            order_list.sort()
            group = []
            if ligandFlag:
                residue_name = str(self._reqObj.getValue('group_id_' + id))
                if not residue_name:
                    if multiGroupFlag:
                        self._message += 'New residue name is missing for group "' + id + '". <br/>\n'
                    else:
                        self._message += 'New residue name is missing. <br/>\n'
                    #
                    continue
                #
                group.append(residue_name)
            #
            for i in order_list:
                group.append(int_order_dic[i][0])
            #
            self.__groups.append(group)
        #

    def __processList(self, token, order_dic, group_dic):
        """ Process group list
        """
        tlist = self._reqObj.getValueList(token)
        if not tlist:
            return
        #
        for v in tlist:
            val = str(v)
            name = 'order_' + val
            order_dic[val] = str(self._reqObj.getValue(name))
            name = 'group_' + val
            value = str(self._reqObj.getValue(name))
            if value in group_dic:
                group_dic[value].append(val)
            else:
                group_dic[value] = [val]
            #
        #
