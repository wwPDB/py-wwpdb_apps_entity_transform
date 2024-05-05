##
# File:  FormPreProcess.py
# Date:  02-Dec-2012
# Updates:
##
"""
Check the input value(s) and make sure they are appropriate.

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
#


class FormPreProcess(object):
    """ Class responsible for checking the input value(s)

    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        self.__reqObj = reqObj
        #
        self.__submitValue = str(self.__reqObj.getValue('submit'))
        self.__entityList = self.__reqObj.getValueList('entity')
        self.__chainList = self.__reqObj.getValueList('chain')
        self.__ligandList = self.__reqObj.getValueList('ligand')
        self.__groupList = self.__reqObj.getValueList('group')
        self.__splitPolymerResidue = str(self.__reqObj.getValue('split_polymer_residue'))
        self.__chainID = str(self.__reqObj.getValue('chain_id'))
        self.__resName = str(self.__reqObj.getValue('res_name'))
        self.__resNum = str(self.__reqObj.getValue('res_num'))
        #
        self.__errorMessage = ''
        #
        self.__labelDic = {}
        self.__valueDic = {}
        self.__preProcessForm()
        #

    def __preProcessForm(self):
        #
        # Check for non standard residue
        #
        if self.__submitValue == 'Split with chopper':
            hasResidueSelected = False
            if self.__splitPolymerResidue or (self.__chainID and self.__resName and self.__resNum):
                hasResidueSelected = True
            #
            if not hasResidueSelected:
                self.__errorMessage = 'No residue selected'
            #
            return
        #
        # Check no values
        #
        if (not self.__entityList) and (not self.__chainList) and \
           (not self.__ligandList) and (not self.__groupList):
            self.__errorMessage = 'No polymer/non-polymer selected'
            return
        #
        # Check selections
        #
        if ((self.__submitValue == 'Merge to polymer') or (self.__submitValue == 'Merge/Split with chopper')) and self.__entityList:
            self.__errorMessage = 'For "' + self.__submitValue + '" option, only ' + \
                'polymer chain ID(s) and/or ligand ID(s) selection are allowed.'
            return
        elif ((self.__submitValue == 'Split polymer to polymer(s)/non-polymer(s)') or (self.__submitValue == 'Remove residue(s) from polymer sequence(s)')) and \
             (self.__chainList or self.__ligandList or self.__groupList):
            self.__errorMessage = 'For "' + self.__submitValue + '" option, only polymer entity ID(s) selection are allowed.'
            return
        elif (self.__submitValue == 'Merge to ligand') and (self.__entityList or self.__chainList or self.__groupList):
            self.__errorMessage = 'For "' + self.__submitValue + '" option, only ligand ID(s) selection are allowed.'
            return
        #
        # Check Group IDs for 'Merge to polymer' and 'Merge/Split with chopper'
        #
        if self.__submitValue == 'Split polymer to polymer(s)/non-polymer(s)':
            return
        #
        self.__chainList = self.__getLabelDic(self.__chainList, 'Chain ')
        self.__ligandList = self.__getLabelDic(self.__ligandList, 'Residue ')
        self.__groupList = self.__getLabelDic(self.__groupList, 'GROUP_')
        #
        dic = {}
        group_id = []
        self.__getUsrDefinedgroup(self.__chainList, 'chain_', group_id, dic)
        self.__getUsrDefinedgroup(self.__ligandList, 'ligand_', group_id, dic)
        self.__getUsrDefinedgroup(self.__groupList, 'group_', group_id, dic)
        #
        if not group_id:
            if ((self.__submitValue == 'Merge to polymer') or (self.__submitValue == 'Merge to ligand')) and \
               (len(self.__labelDic) == 1):
                self.__errorMessage = 'Only one instance "' + list(self.__labelDic.keys())[0] + '" is selected.'
            #
            return
        #
        if (len(group_id) > 1) and (self.__submitValue == 'Merge/Split with chopper'):
            self.__errorMessage = 'Multiple User defind Group IDs are assigned. For "Merge/Split ' \
                + 'with chopper" option, only one User defind Group can be processed each time.\n'
            return
        #
        for lid, label in self.__labelDic.items():
            if lid not in self.__valueDic:
                self.__errorMessage += 'No User defind Group ID assigned for "' + label + '".<br/>\n'
            #
        #
        if ((self.__submitValue == 'Merge to polymer') or (self.__submitValue == 'Merge to ligand')):
            for gid in sorted(list(dic.keys())):
                if len(dic[gid]) == 1:
                    self.__errorMessage += 'For "User defind Group ' + gid + '", only one instance "' + dic[gid][0] + '" is selected.<br/>\n'
                #
            #
        #

    def __getLabelDic(self, instList, label_prefix):
        if not instList:
            return
        #
        new_list = []
        for v in instList:
            val = str(v)
            slist = val.split(',')
            if len(slist) > 1:
                val = ','.join(slist[1:])
                self.__labelDic[val] = label_prefix + slist[0]
                new_list.append(val)
            else:
                new_list.append(val)
                list1 = slist[0].split('_')
                if len(list1) > 1:
                    self.__labelDic[val] = label_prefix + ' '.join(list1)
                else:
                    self.__labelDic[val] = label_prefix + val
                #
            #
        #
        return new_list

    def __getUsrDefinedgroup(self, instList, key_prefix, group_id, dic):
        if not instList:
            return
        #
        for v in instList:
            name = key_prefix + str(v)
            value = str(self.__reqObj.getValue(name))
            if not value:
                continue
            #
            label = v
            if v in self.__labelDic:
                label = self.__labelDic[v]
            #
            self.__valueDic[v] = value
            #
            if value in dic:
                dic[value].append(label)
            else:
                dic[value] = [label]
                group_id.append(value)
            #
        #

    def getMessage(self):
        return self.__errorMessage
