##
# File:  PrdSummaryDepict.py
# Date:  09-Oct-2012
# Updates:
##
"""
Create HTML depiction for PRD search summary.

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

class PrdSummaryDepict(DepictBase):
    """ Class responsible for generating HTML depiction of PRD search results.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(PrdSummaryDepict, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__propertyList = ( ( 'Name', 'name' ), ( 'Residue number', 'residue_number' ), \
                                ( 'Chain ID(s)', 'pdb_chain_ids' ), ( 'Type', 'polymer_type' ) )
        #
        self.__typeMap = { 'polydeoxyribonucleotide' : 'DNA', 'polydeoxyribonucleotide/polyribonucleotide hybrid' : 'DNA/RNA', \
                           'polypeptide(D)' : 'Protein', 'polypeptide(L)' : 'Protein', 'polyribonucleotide' : 'RNA', \
                           'polysaccharide(D)' : 'Sugar', 'polysaccharide(L)' : 'Sugar' }
        #
        #
        self.__data = []
        self.__image_data = []
        #
        self.__matchResultFlag = {}
        self.__graphmatchResultFlag = False
        self.__combResidueFlag = False
        #
        self.__splitPolymerResidueFlag = False

    def DoRenderSummaryPage(self):
        self.__readEntityData()
        self.__readNonPolymerData()
        self.__readGroupData()
        self.__readmatchResult()
        self.__readSplitMergePolymerResidueResult()
        self.__generateImage()
        #
        input_data = 'sessionid=' + self._sessionId + '&identifier=' + self._identifier + '&pdbid=' + self._pdbId
        #
        text = '<ul>\n'
        #
        text += self.__depiction(self.__data) + '\n'
        #
        text += '<li><a class="fltlft" href="/service/entity/summary_view?' + input_data + '" target="_blank"> Access to split or merge </a></li>\n'
        #
        if self.__splitPolymerResidueFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
                  + '&type=split" target="_blank"> Split modified amino acid residue to standard amino acid residue + modification in polymer </a></li>\n'
        #
        if self.__combResidueFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
                  + '&type=merge" target="_blank"> Merge standard amino acid residue + modification to modified amino acid residue in polymer </a></li>\n' 
        #
        if self.__matchResultFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data + '" target="_blank"> View All Search Result(s) </a></li>\n'
        # 
        if self.__graphmatchResultFlag:
            text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
                  + '&type=match" target="_blank"> Update Coordinate File with Match Result(s) </a></li>\n' 
        #
        text += '<li><a class="fltlft" href="/service/entity/result_view?' + input_data \
              + '&type=input" target="_blank"> Update Coordinate File with Input IDs </a></li>\n'
        #
        text += '<li><a class="fltlft" href="/service/entity/download_file?' + input_data + '" target="_blank"> Download Files </a></li>\n'
        #
        text += '</ul>\n'
        #
        return text

    def __readEntityData(self):
        elist = self._cifObj.getValueList('pdbx_entity_info')
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
        plist = self._cifObj.getValueList('pdbx_polymer_info')
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
        elist = self._cifObj.getValueList('pdbx_non_polymer_info')
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
        elist = self._cifObj.getValueList('pdbx_group_info')
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
        elist = self._cifObj.getValueList('pdbx_match_result')
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
        slist = self._cifObj.getValueList('pdbx_split_polymer_residue_info')
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
        mlist = self._cifObj.getValueList('pdbx_merge_polymer_residue_info')
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
        iGenerator = ImageGenerator(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        iGenerator.run(self.__image_data)

    def __depiction(self, datalist):
        text = ''
        if not datalist:
            return text
        #
        for d in datalist:
            myD = {}
            myD['id'] = d['id']
            myD['text'] = d['text']
            if d.has_key('list_text'):
                list_text = '<li>\n' + d['list_text'] + '</li>\n'
                if d.has_key('list'):
                    list_text += self.__depictInstanceTable(d['list'])
                myD['list'] = list_text
            elif d.has_key('list'):
                myD['list'] = self.__depiction(d['list'])
            else:
                myD['list'] = ''
            text += '<li>\n' + self._processTemplate('summary_view/expand_list_tmplt.html', myD) + '</li>\n'
        #
        return text

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

    def __depictInstanceTable(self, datalist):
        if not datalist:
            return ''
        #
        text = '<table>\n'
        #
        for d in datalist:
            myD = {}
            myD['sessionid'] = self._sessionId
            myD['identifier'] =  self._identifier
            myD['pdbid' ] = self._pdbId
            myD['instanceid'] = d['id']
            myD['label'] = d['label']
            myD['focus'] = d['focus']
            myD['3d_view'] = self._processTemplate('summary_view/3d_view_tmplt.html', myD)
            myD['2d_view'] = self._processTemplate('summary_view/2d_view_tmplt.html', myD)
            myD['build_prd'] = self._processTemplate('summary_view/build_prd_tmplt.html', myD)
            if self.__matchResultFlag.has_key(d['id']):
                text += self._processTemplate('summary_view/row_with_result_tmplt.html', myD) + '\n'
            elif d['linkage_info'] == 'linked':
                text += self._processTemplate('summary_view/row_tmplt.html', myD) + '\n'
            else:
                if d.has_key('message'):
                    message = d['message'].replace('\n', '<br/>')
                    myD['text'] = '<span class="warninfo">\n<a href="#" title="' + message + '" onclick="return false">\nNot connected</a>\n</span>'
                else:
                    myD['text'] = 'Not connected'
                text += self._processTemplate('summary_view/row_without_2D_view_tmplt.html', myD) + '\n'
        #
        text += '</table>\n'
        return text
