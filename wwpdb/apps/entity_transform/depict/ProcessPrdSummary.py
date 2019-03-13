##
# File:  ProcessPrdSummary.py
# Date:  15-Feb-2019
# Updates:
##
"""
Process PRD search results and generate images.

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

from wwpdb.apps.entity_transform.depict.DepictBase import DepictBase
from wwpdb.apps.entity_transform.utils.ImageGenerator import ImageGenerator
from wwpdb.apps.entity_transform.utils.SummaryCifUtil import SummaryCifUtil

class ProcessPrdSummary(object):
    """ Class responsible for reading PRD search results and generating images.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        self.__reqObj = reqObj
        self.__cifObj = summaryCifObj
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__propertyList = ( ( 'Name', 'name' ), ( 'Residue number', 'residue_number' ), \
                                ( 'Chain ID(s)', 'pdb_chain_ids' ), ( 'Type', 'polymer_type' ) )
        #
        self.__typeMap = { 'polydeoxyribonucleotide' : 'DNA', 'polydeoxyribonucleotide/polyribonucleotide hybrid' : 'DNA/RNA', \
                           'polypeptide(D)' : 'Protein', 'polypeptide(L)' : 'Protein', 'polyribonucleotide' : 'RNA', \
                           'polysaccharide(D)' : 'Sugar', 'polysaccharide(L)' : 'Sugar' }
        #
        self.__topDirPath = None
        self.__image_data = []
        #
        self.__data = []
        self.__matchResultFlag = {}
        self.__graphmatchResultFlag = False
        self.__combResidueFlag = False
        self.__splitPolymerResidueFlag = False

    def setTopDirPath(self, topPath):
        self.__topDirPath = topPath

    def setPrdSummaryFile(self, summaryfilePath):
        self.__cifObj = SummaryCifUtil(summaryFile=summaryfilePath, verbose=self.__verbose, log=self.__lfh)

    def run(self, imageFlag=True):
        if not self.__cifObj:
            return
        #
        self.__readEntityData()
        self.__readNonPolymerData()
        self.__readGroupData()
        self.__readmatchResult()
        self.__readSplitMergePolymerResidueResult()
        if imageFlag:
            self.__generateImage()
        #

    def getPrdData(self):
        return self.__data

    def getMatchResultFlag(self):
        return self.__matchResultFlag

    def getGraphmatchResultFlag(self):
        return self.__graphmatchResultFlag

    def getCombResidueFlag(self):
        return self.__combResidueFlag

    def getSplitPolymerResidueFlag(self):
        return self.__splitPolymerResidueFlag

    def __readEntityData(self):
        elist = self.__cifObj.getValueList('pdbx_entity_info')
        if not elist:
            return
        #
        nucleotide = {}
        for d in elist:
            if (not d.has_key('entity_id')) or (not d.has_key('polymer_type')):
                continue
            #
            if (d['polymer_type'].lower() == 'polyribonucleotide') or (d['polymer_type'].lower() == 'polydeoxyribonucleotide'):
                nucleotide[d['entity_id']] = 'yes'
            #
        #
        pmap = {}
        plist = self.__cifObj.getValueList('pdbx_polymer_info')
        if plist:
            for d in plist:
                if (not d.has_key('pdb_chain_id')) or (not d.has_key('polymer_id')) or (not d.has_key('linkage_info')):
                    continue
                #
                pmap[d['pdb_chain_id']] = d
                #
                # Skip generating images for DNA/RNA polymers
                #
                if d.has_key('entity_id') and nucleotide.has_key(d['entity_id']):
                    continue
                #
                if d['linkage_info'] == 'linked':
                    self.__image_data.append( ( d['polymer_id'], 'CHAIN_' + d['pdb_chain_id']) )
                #
            #
        #
        entitylist = []
        for d in elist:
            type = ''
            if d.has_key('type'):
                type = d['type']
            if type != 'polymer':
                continue
            #
            entity_id = ''
            if d.has_key('entity_id'):
                entity_id = d['entity_id']
            #
            properties = {}
            for prolist in self.__propertyList:
                if (not d.has_key(prolist[1])) or (not d[prolist[1]]):
                    continue
                #
                if prolist[1] == 'polymer_type':
                    if self.__typeMap.has_key(d[prolist[1]]):
                        properties[prolist[0]] = self.__typeMap[d[prolist[1]]] + ' ( ' + d[prolist[1]] + ' )'
                    else:
                        properties[prolist[0]] = d[prolist[1]]
                    #
                else:
                    properties[prolist[0]] = d[prolist[1]]
                #
            #
            if (not entity_id) or (not properties.has_key('Chain ID(s)')):
                continue
            #
            seq = ''
            if d.has_key('one_letter_seq'):
                seq = '<br/>' + self.__processingOneLetterSeq(d['one_letter_seq'])
            elif d.has_key('three_letter_seq'):
                seq = d['three_letter_seq']
            #
            text = ''
            for prolist in self.__propertyList:
                if not properties.has_key(prolist[0]):
                    continue
                #
                if text:
                    text += ', '
                #
                text += prolist[0] + ': <span style="color:red;">' + properties[prolist[0]] + '</span>'
            #
            dic = {}
            dic['id'] = 'entity_' + entity_id
            dic['text'] = 'Entity ' + entity_id + ' ( ' + text + ' )'
            dic['list_text'] = 'Residues: ' + seq
            #
            polymerlist = []
            flag = False
            clist = properties['Chain ID(s)'].split(',')
            for c in clist:
                if flag:
                    continue
                #
                if not pmap.has_key(c):
                    continue
                #
                if pmap[c]['linkage_info'] == 'big_polymer':
                    flag = True
                    continue
                #
                pdic = {}
                pdic['id'] =  pmap[c]['polymer_id']
                pdic['linkage_info'] = pmap[c]['linkage_info']
                if pmap[c].has_key('message'):
                    pdic['message'] = pmap[c]['message']
                pdic['label'] = 'CHAIN_' + c
                pdic['focus'] = pmap[c]['focus']
                polymerlist.append(pdic)
            #
            if polymerlist:
                dic['list'] = polymerlist
            #
            entitylist.append(dic)
        #
        if not entitylist:
            return
        #
        dic = {}
        dic['id'] = 'polymers'
        dic['text'] = 'Polymers'
        dic['list'] = entitylist
        self.__data.append(dic)

    def __readNonPolymerData(self):
        elist = self.__cifObj.getValueList('pdbx_non_polymer_info')
        if not elist:
            return
        #
        nonpolymermap = {}
        for d in elist:
            if (not d.has_key('instance_id')) or (not d.has_key('residue_id')) or (not d.has_key('linkage_info')):
                continue
            #
            if d['linkage_info'] == 'linked':
                self.__image_data.append( ( d['instance_id'], d['instance_id'] ) )
            #
            if nonpolymermap.has_key(d['residue_id']):
                nonpolymermap[d['residue_id']].append(d)
            else:
                list = []
                list.append(d)
                nonpolymermap[d['residue_id']] = list
            #
        #
        if not nonpolymermap:
            return
        #
        list = []
        for k,v in nonpolymermap.items():
            list.append(k)
        list.sort()
        #
        nonpolymerlist = []
        for k in list:
            v = nonpolymermap[k]
            count = len(v)
            text = k + ' (' + str(count) + ' '
            list_text = ''
            if count > 1:
                text += 'residues)'
                list_text += 'Residues:'
            else:
                text += 'residue)'
                list_text += 'Residue:'
            #
            dic = {}
            dic['id'] = k
            dic['text'] = text
            instlist = []
            for d in v:
                list_text += ' ' + d['instance_id']
                pdic = {}
                pdic['id'] = d['instance_id']
                pdic['linkage_info'] = d['linkage_info']
                if d.has_key('message'):
                    pdic['message'] = d['message']
                pdic['label'] = d['instance_id']
                pdic['focus'] = d['focus']
                instlist.append(pdic)
            #
            dic['list_text'] = list_text
            if instlist:
                dic['list'] = instlist
            nonpolymerlist.append(dic)
        # 
        if not nonpolymerlist:
            return
        #
        dic = {}
        dic['id'] = 'nonpolymers'
        dic['text'] = 'Non-polymers'
        dic['list'] = nonpolymerlist
        self.__data.append(dic)

    def __readGroupData(self):
        elist = self.__cifObj.getValueList('pdbx_group_info')
        if not elist:
            return
        #
        grouplist = []
        for d in elist:
            if (not d.has_key('group_id')) or (not d.has_key('descriptor')) or (not d.has_key('residues')) or (not d.has_key('linkage_info')):
                continue
            #
            if d['linkage_info'] == 'linked':
                self.__image_data.append( ( d['group_id'], d['group_id'].upper() ) )
            #
            dic = {}
            dic['id'] = 'g_' + d['group_id']
            dic['text'] = d['group_id'].upper() + ' (' + d['descriptor'] + ')'
            dic['list_text'] = 'Residues: ' + d['residues']
            instlist = []
            pdic = {}
            pdic['id'] = d['group_id']
            pdic['linkage_info'] = d['linkage_info']
            if d.has_key('message'):
                pdic['message'] = d['message']
            pdic['label'] = d['group_id'].upper()
            pdic['focus'] = d['focus']
            instlist.append(pdic)
            dic['list'] = instlist
            grouplist.append(dic)
        #
        if not grouplist:
            return
        #
        dic = {}
        dic['id'] = 'groups'
        dic['text'] = 'Connected residues(Groups)'
        dic['list'] = grouplist
        self.__data.append(dic)

    def __readmatchResult(self):
        elist = self.__cifObj.getValueList('pdbx_match_result')
        if not elist:
            return
        #
        for d in elist:
            if not d.has_key('inst_id'):
                continue
            #
            if d['inst_id'].startswith('merge'):
                self.__combResidueFlag = True
            else:
                self.__matchResultFlag[d['inst_id']] = 'yes'
                #
                if d.has_key('method') and d['method'] == 'graph':
                    self.__graphmatchResultFlag = True
                #
            #
        #

    def __readSplitMergePolymerResidueResult(self):
        slist = self.__cifObj.getValueList('pdbx_split_polymer_residue_info')
        if slist:
            self.__splitPolymerResidueFlag = True
            for d in slist:
                if (not d.has_key('instance_id')) or (not d.has_key('linkage_info')):
                    continue
                #
                if d['linkage_info'] == 'linked':
                    self.__image_data.append( ( d['instance_id'], d['instance_id'] ) )
                #
            #
        #
        mlist = self.__cifObj.getValueList('pdbx_merge_polymer_residue_info')
        if mlist:
            for d in mlist:
                if (not d.has_key('merge_id')) or (not d.has_key('linkage_info')):
                    continue
                #
                if d['linkage_info'] == 'linked':
                    self.__image_data.append( ( d['merge_id'], d['merge_id'].upper() ) )
                #
            #
        #

    def __generateImage(self):
        if not self.__image_data:
            return
        #
        iGenerator = ImageGenerator(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        if self.__topDirPath:
            iGenerator.setSessionPath(path=self.__topDirPath)
        #
        iGenerator.run(self.__image_data)

    def __processingOneLetterSeq(self, input_seq):
        seq = input_seq.replace('\n', '').replace(' ', '').replace('\t', '')
        output_seq = ''
        count = 0
        startParenthesisFlag = False
        for letter in seq:
            output_seq += letter
            if letter == '(':
                startParenthesisFlag = True
            elif letter == ')':
                startParenthesisFlag = False
            #
            count += 1
            if (count >= 80) and (not startParenthesisFlag):
                output_seq += '<br />\n'
                count = 0
            #
        #
        return output_seq.replace('(', '<span style="color:red;">(').replace(')', ')</span>')
