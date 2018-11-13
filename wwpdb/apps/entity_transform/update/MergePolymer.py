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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import os, sys, string, traceback

from wwpdb.apps.entity_transform.update.UpdateBase   import UpdateBase

class MergePolymer(UpdateBase):
    """ Class responsible for merging polymer(s) in coordinate cif file.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(MergePolymer, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__groups = []

    def updateFile(self):
        """ Update coordinate cif file
        """
        self.__getGroups()
        if self._message or not self.__groups:
            return
        #
        options = ''
        for group in self.__groups:
            options += ' -group ' + ','.join(group) + ' '
        #
        self._runUpdateScript('MergePolymer', 'Merge to polymer', 'run-merge', options)

    def __getGroups(self):
        """ Get groups
        """
        order_dic = {}
        group_dic = {}
        chainList   = self._reqObj.getValueList('chain')
        self.__processList('chain', order_dic, group_dic)
        self.__processList('ligand', order_dic, group_dic)
        #
        for id,list in group_dic.items():
            num = len(list)
            int_order_dic = {}
            for v in list:
                if not order_dic.has_key(v):
                    continue
                #
                order = int(order_dic[v])
                if int_order_dic.has_key(order):
                    int_order_dic[order].append(v)
                else:
                    list1 = []
                    list1.append(v)
                    int_order_dic[order] = list1
                #
            #
            # Check unique order numbering
            #
            order_list = []
            for k,list2 in int_order_dic.items():
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
                    else:
                        if len(list3) > 1:
                            text += 'Ligand ' + v
                        else:
                            text += 'Chain ' + v
                self._message += text + ' have same order number "' + str(k) + '". <br/>\n'
            #
            # Check missing order numbering
            #
            for i in xrange(0, len(list)):
                j = i + 1
                if int_order_dic.has_key(j):
                    continue
                self._message += 'In group ' + id + ', order number "' + str(j) + '" is missing. <br/>\n' 
            #
            if self._message:
                continue
            #
            # Reorder group based on order number
            #
            order_list.sort()
            group = []
            for i in order_list:
                group.append(int_order_dic[i][0])
            #
            self.__groups.append(group)
   
    def __processList(self, token, order_dic, group_dic):
        """ Process group list
        """
        list = self._reqObj.getValueList(token)
        if not list:
            return
        #
        for v in list:
            val = str(v)
            name = 'order_' + val
            order_dic[val] = str(self._reqObj.getValue(name))
            name = 'group_' + val
            value = str(self._reqObj.getValue(name))
            if group_dic.has_key(value):
                group_dic[value].append(val)
            else:
                list1 = []
                list1.append(val)
                group_dic[value] = list1
            #
        #
