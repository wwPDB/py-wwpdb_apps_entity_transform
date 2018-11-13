##
# File:  SummaryCifUtil.py
# Date:  17-Oct-2012
# Updates:
##
"""
Read and handle search summary cif file.

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

from wwpdb.utils.rcsb.mmCIFUtil import mmCIFUtil
#

class SummaryCifUtil(object):
    """ Class responsible for handling search summary cif file.
    """
    def __init__(self, summaryFile=None, verbose=False, log=sys.stderr):
        self.__verbose=verbose
        self.__lfh=log
        self.__cifObj = mmCIFUtil(filePath=summaryFile)
        #
        self.__seqs = {}
        self.__labels = {}
        self.__linkage_info = {}
        self.__focus = {}
        self.__instIds = []
        self.__getSeqsFlag = False
        #
        self.__matchInstIds = []
        self.__matchResults = {}
        self.__getMatchResultsFlag = False

    def getValueList(self, category):
        return self.__cifObj.GetValue(category)

    def getPdbId(self):
        return self.__cifObj.GetSingleValue('entry', 'id')

    def getDepId(self):
        return self.__cifObj.GetSingleValue('entry', 'depid')

    def getEntryIds(self):
        depid = self.getDepId()
        pdbid = self.getPdbId()
        if depid and pdbid:
            return depid.upper() + '/' + pdbid.upper()
        elif depid:
            return depid.upper()
        elif pdbid:
            return pdbid.upper()
        #
        return ''

    def getFileId(self):
        return self.__cifObj.GetSingleValue('entry', 'file')

    def getTitle(self):
        return self.__cifObj.GetSingleValue('struct', 'title')

    def getSeqs(self):
        self.__getSeqs()
        return self.__seqs

    def getSeq(self, instId):
        self.__getSeqs()
        if self.__seqs.has_key(instId):
            return self.__seqs[instId]
        #
        return ''

    def getLabels(self):
        self.__getSeqs()
        return self.__labels

    def getLabel(self, instId):
        self.__getSeqs()
        if self.__labels.has_key(instId):
            return self.__labels[instId]
        #
        return ''

    def getLinkageInfo(self, instId):
        self.__getSeqs()
        if self.__linkage_info.has_key(instId):
            return self.__linkage_info[instId]
        #
        return ''

    def getFocus(self, instId):
        self.__getSeqs()
        if self.__focus.has_key(instId):
            return self.__focus[instId]
        #
        return ''

    def getAllInstIds(self):
        self.__getSeqs()
        return self.__instIds

    def getMatchInstIds(self):
        self.__getMatchResults()
        return self.__matchInstIds

    def getMatchResults(self):
        self.__getMatchResults()
        return self.__matchResults

    def getMatchResult(self, instId):
        self.__getMatchResults()
        if self.__matchResults.has_key(instId):
            return self.__matchResults[instId]
        #
        return {}

    def __getSeqs(self):
        if self.__getSeqsFlag:
            return
        #
        self.__getSeqsFlag = True
        #
        category_item = [ [ 'pdbx_polymer_info',      'polymer_id',  'three_letter_seq', 'linkage_info', 'focus' ], \
                          [ 'pdbx_non_polymer_info',  'instance_id', 'residue_id',       'linkage_info', 'focus' ], \
                          [ 'pdbx_group_info',        'group_id',    'residues',         'linkage_info', 'focus' ], \
                          [ 'pdbx_merge_polymer_residue_info', 'merge_id', 'residues',   'linkage_info', 'focus' ] ]
        #
        for d in category_item:
            elist = self.__cifObj.GetValue(d[0])
            if not elist:
                continue
            #
            for e in elist:
                if (not e.has_key(d[1])) or (not e.has_key(d[2])):
                    continue
                #
                self.__instIds.append(e[d[1]])
                if d[0] == 'pdbx_non_polymer_info':
                    self.__seqs[e[d[1]]] = e[d[1]]
                else:
                    self.__seqs[e[d[1]]] = e[d[2]]
                #
                if d[0] == 'pdbx_polymer_info':
                    if e.has_key('pdb_chain_id'):
                        self.__labels[e[d[1]]] = 'CHAIN_' + e['pdb_chain_id']
                    else:
                        elf.__labels[e[d[1]]] = e[d[1]].upper()
                elif d[0] == 'pdbx_non_polymer_info':
                    self.__labels[e[d[1]]] = e[d[1]]
                elif (d[0] == 'pdbx_group_info') or (d[0] == 'pdbx_merge_polymer_residue_info'):
                    self.__labels[e[d[1]]] = e[d[1]].upper()
                #
                if e.has_key(d[3]):
                    self.__linkage_info[e[d[1]]] = e[d[3]]
                #
                if e.has_key(d[4]):
                    self.__focus[e[d[1]]] = e[d[4]]
                #
            #
        #

    def __getMatchResults(self):
        if self.__getMatchResultsFlag:
            return
        #
        self.__getMatchResultsFlag = True
        elist = self.__cifObj.GetValue('pdbx_match_result')
        if not elist:
            return
        #
        for d in elist:
            if (not d.has_key('inst_id')) or \
               (not d.has_key('id')) or \
               (not d.has_key('type')) or \
               (not d.has_key('method')):
                continue
            #
            m_dic = {}
            m_dic['value'] = d['type']
            if d.has_key('sequence'):
                m_dic['sequence'] = d['sequence']
            id = d['id']
            if id[:4] == 'PRD_':
                m_dic['prdid'] = id
            else:
                m_dic['ccid'] = id
                if d.has_key('prd_id'):
                    m_dic['prdid'] = d['prd_id']
            #
            if self.__matchResults.has_key(d['inst_id']):
                if self.__matchResults[d['inst_id']].has_key(d['method']):
                    self.__matchResults[d['inst_id']][d['method']].append(m_dic)
                else:
                    list = []
                    list.append(m_dic)
                    self.__matchResults[d['inst_id']][d['method']] = list
            else:
                self.__matchInstIds.append(d['inst_id'])
                list = []
                list.append(m_dic)
                dic = {}
                dic[d['method']] = list
                self.__matchResults[d['inst_id']] = dic
            #
        #
