##
# File:  LinkUtil.py
# Date:  10-Dec-2012
# Updates:
##
"""
Read and handle link records.

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


class LinkUtil(object):
    """ Class responsible for handling link records.

    """
    def __init__(self, cifObj=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        self.__cifObj = cifObj
        #
        self.__links = {}
        self.__readLinkData()
        #
        self.__getPolymerLinkData()
        #
        self.__gerGroupLinkData()

    def getLinks(self):
        return self.__links

    def __readLinkData(self):
        dlist = self.__cifObj.getValueList('struct_conn')
        if not dlist:
            return
        #
        items1 = ['ptnr1_auth_asym_id', 'ptnr1_auth_comp_id', 'ptnr1_auth_seq_id',
                  'pdbx_ptnr1_PDB_ins_code', 'ptnr1_label_atom_id', 'ptnr1_symmetry',
                  'ptnr2_auth_asym_id', 'ptnr2_auth_comp_id', 'ptnr2_auth_seq_id',
                  'pdbx_ptnr2_PDB_ins_code', 'ptnr2_label_atom_id', 'ptnr2_symmetry']
        items2 = ['ptnr2_auth_asym_id', 'ptnr2_auth_comp_id', 'ptnr2_auth_seq_id',
                  'pdbx_ptnr2_PDB_ins_code', 'ptnr2_label_atom_id', 'ptnr2_symmetry',
                  'ptnr1_auth_asym_id', 'ptnr1_auth_comp_id', 'ptnr1_auth_seq_id',
                  'pdbx_ptnr1_PDB_ins_code', 'ptnr1_label_atom_id', 'ptnr1_symmetry']
        #
        index = {}
        for d in dlist:
            link1 = self.__getLink(d, items1)
            link2 = self.__getLink(d, items2)
            if (not link1) or (not link2):
                continue
            #
            key1 = '_'.join(link1)
            key2 = '_'.join(link2)
            if key1 in index or key2 in index:
                continue
            #
            index[key1] = 'yes'
            index[key2] = 'yes'
            #
            self.__addLink(link1)
            self.__addLink(link2)
            key1 = '_'.join(link1[0:4])
            key2 = '_'.join(link2[0:4])

        #

    def __getLink(self, dic, items):
        has_value = False
        rlist = []
        for item in items:
            val = ''
            if item in dic:
                val = dic[item]
                has_value = True
            #
            rlist.append(val)
        #
        if not has_value:
            rlist = []
        #
        return rlist

    def __addLink(self, link):
        res_key = '_'.join(link[0:4])
        if res_key in self.__links:
            self.__links[res_key].append(link)
        else:
            link_list = []
            link_list.append(link)
            self.__links[res_key] = link_list
        #

    def __getPolymerLinkData(self):
        if not self.__links:
            return
        #
        dlist = self.__cifObj.getValueList('pdbx_poly_seq_scheme')
        if not dlist:
            return
        #
        items = ['pdb_strand_id', 'pdb_mon_id', 'pdb_seq_num', 'pdb_ins_code']
        #
        index = {}
        for d in dlist:
            has_value = False
            v_list = []
            for item in items:
                val = ''
                if item in d:
                    val = d[item]
                    has_value = True
                #
                v_list.append(val)
            #
            if not has_value:
                continue
            #
            res_key = '_'.join(v_list)
            if res_key not in self.__links:
                continue
            #
            for link in self.__links[res_key]:
                key1 = '_'.join(link[0:6])
                key2 = '_'.join(link[6:])
                #
                key3 = key1 + '_' + key2
                if key3 in index:
                    continue
                #
                key4 = key2 + '_' + key1
                if key4 in index:
                    continue
                #
                index[key3] = 'yes'
                index[key4] = 'yes'
                #
                if v_list[0] in self.__links:
                    self.__links[v_list[0]].append(link)
                else:
                    llist = []
                    llist.append(link)
                    self.__links[v_list[0]] = llist
                #
            #
        #

    def __gerGroupLinkData(self):
        if not self.__links:
            return
        #
        dlist = self.__cifObj.getValueList('pdbx_group_list')
        if not dlist:
            return
        #
        # items = ['pdb_strand_id', 'pdb_mon_id', 'pdb_seq_num', 'pdb_ins_code']
        #
        index = {}
        for d in dlist:
            if 'component_ids' not in d:
                continue
            #
            index = {}
            group = str(d['component_ids'])
            glist = group.split(',')
            link_list = []
            for component in glist:
                if component not in self.__links:
                    continue
                #
                for link in self.__links[component]:
                    key1 = '_'.join(link[0:6])
                    key2 = '_'.join(link[6:])
                    #
                    key3 = key1 + '_' + key2
                    if key3 in index:
                        continue
                    #
                    key4 = key2 + '_' + key1
                    if key4 in index:
                        continue
                    #
                    index[key3] = 'yes'
                    index[key4] = 'yes'
                    #
                    link_list.append(link)
                    #
                #
            #
            if link_list:
                self.__links[group] = link_list
            #
        #
