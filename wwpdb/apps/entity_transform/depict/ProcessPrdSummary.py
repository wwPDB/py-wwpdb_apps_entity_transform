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
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import copy
import sys

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
        self.__propertyList = (('Name', 'name'), ('Residue number', 'residue_number'),
                               ('Chain ID(s)', 'pdb_chain_ids'), ('Type', 'polymer_type'))
        #
        self.__typeMap = {'polydeoxyribonucleotide' : 'DNA', 'polydeoxyribonucleotide/polyribonucleotide hybrid' : 'DNA/RNA',
                          'polypeptide(D)' : 'Protein', 'polypeptide(L)' : 'Protein', 'polyribonucleotide' : 'RNA',
                          'polysaccharide(D)' : 'Sugar', 'polysaccharide(L)' : 'Sugar'}
        #
        self.__topDirPath = None
        self.__image_data = []
        #
        self.__data = []
        self.__action_required_data = []
        self.__other_data = []
        #
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
        if self.__action_required_data:
            dic = {}
            dic["id"] = "action"
            dic["arrow"] = "ui-icon-circle-arrow-s"
            dic["text"] = "Action required:"
            dic["display"] = "block"
            dic["list"] = self.__action_required_data
            self.__data.append(dic)
            #
            if self.__other_data:
                # dic = {}
                # dic["id"] = "other"
                # dic["arrow"] = "ui-icon-circle-arrow-e"
                # dic["text"] = "Other entities:"
                # dic["display"] = "none"
                # dic["list"] = self.__other_data
                # self.__data.append(dic)
                self.__data.extend(self.__other_data)
            #
        else:
            self.__data = self.__other_data
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
        elist = self.__cifObj.getValueList("pdbx_entity_info")
        if not elist:
            return
        #
        nucleotide = {}
        for d in elist:
            if ("entity_id" not in d) or ("polymer_type" not in d):
                continue
            #
            if (d["polymer_type"].lower() == "polyribonucleotide") or (d["polymer_type"].lower() == "polydeoxyribonucleotide"):
                nucleotide[d["entity_id"]] = "yes"
            #
        #
        pmap = {}
        plist = self.__cifObj.getValueList("pdbx_polymer_info")
        if plist:
            for d in plist:
                if ("pdb_chain_id" not in d) or ("polymer_id" not in d) or ("linkage_info" not in d):
                    continue
                #
                pmap[d["pdb_chain_id"]] = d
                #
                # Skip generating images for DNA/RNA polymers
                #
                if "entity_id" in d and d["entity_id"] in nucleotide:
                    continue
                #
                if d["linkage_info"] == "linked":
                    self.__image_data.append((d["polymer_id"], "CHAIN_" + d["pdb_chain_id"]))
                #
            #
        #
        for polymerTup in (("polymer", "polymers", "Polymers"), ("branched", "oligosaccharide", "Oligosaccharides")):
            action_entitylist = []
            other_entitylist = []
            for d in elist:
                if ("type" not in d) or (d["type"] != polymerTup[0]):
                    continue
                #
                entity_id = ""
                if "entity_id" in d:
                    entity_id = d["entity_id"]
                #
                action_required = ""
                if "action_required" in d:
                    action_required = d["action_required"]
                #
                properties = {}
                for prolist in self.__propertyList:
                    if (prolist[1] not in d) or (not d[prolist[1]]):
                        continue
                    #
                    if prolist[1] == "polymer_type":
                        if d[prolist[1]] in self.__typeMap:
                            properties[prolist[0]] = self.__typeMap[d[prolist[1]]] + " ( " + d[prolist[1]] + " )"
                        else:
                            properties[prolist[0]] = d[prolist[1]]
                        #
                    else:
                        properties[prolist[0]] = d[prolist[1]]
                    #
                #
                if (not entity_id) or ("Chain ID(s)" not in properties):
                    continue
                #
                seq = ""
                colorResMap = {}
                if ("color_res_list" in d) and d["color_res_list"]:
                    colorSplitList = d["color_res_list"].replace("\n", "").replace(" ", "").replace("\t", "").split("|")
                    for colorList in colorSplitList:
                        colonSplitList = colorList.split(":")
                        if len(colonSplitList) == 2:
                            colorResMap[colonSplitList[0]] = colonSplitList[1].split(",")
                        #
                    #
                #
                if "one_letter_seq" in d:
                    seq = "<br/>" + self.__processingOneLetterSeq(d["one_letter_seq"], colorResMap)
                elif "three_letter_seq" in d:
                    seq = self.__processingThreeLetterSeq(d["three_letter_seq"], colorResMap)
                #
                text = ""
                for prolist in self.__propertyList:
                    if prolist[0] not in properties:
                        continue
                    #
                    if text:
                        text += ", "
                    #
                    # text += prolist[0] + ": <span style="color:red;">" + properties[prolist[0]] + "</span>"
                    text += prolist[0] + ": " + properties[prolist[0]]
                #
                dic = {}
                dic["id"] = "entity_" + entity_id
                dic["text"] = "Entity " + entity_id + " ( " + text + " )"
                dic["list_text"] = "Residues: " + seq
                #
                polymerlist = []
                flag = False
                clist = properties["Chain ID(s)"].split(",")
                for c in clist:
                    if flag:
                        continue
                    #
                    if c not in pmap:
                        continue
                    #
                    if pmap[c]["linkage_info"] == "big_polymer":
                        flag = True
                        continue
                    #
                    pdic = {}
                    pdic["id"] = pmap[c]["polymer_id"]
                    pdic["linkage_info"] = pmap[c]["linkage_info"]
                    if "message" in pmap[c]:
                        pdic["message"] = pmap[c]["message"]
                    pdic["label"] = "CHAIN_" + c
                    pdic["focus"] = pmap[c]["focus"]
                    polymerlist.append(pdic)
                #
                if polymerlist:
                    dic["list"] = polymerlist
                #
                dic["arrow"] = "ui-icon-circle-arrow-e"
                dic["display"] = "none"
                other_entitylist.append(dic)
                #
                if action_required == "Y":
                    act_dic = copy.deepcopy(dic)
                    act_dic["arrow"] = "ui-icon-circle-arrow-s"
                    act_dic["display"] = "block"
                    action_entitylist.append(act_dic)
                #
            #
            if action_entitylist:
                dic = {}
                dic["id"] = polymerTup[1]
                dic["arrow"] = "ui-icon-circle-arrow-s"
                dic["text"] = polymerTup[2]
                dic["display"] = "block"
                dic["list"] = action_entitylist
                self.__action_required_data.append(dic)
            #
            if other_entitylist:
                dic = {}
                dic["id"] = polymerTup[1]
                dic["arrow"] = "ui-icon-circle-arrow-e"
                dic["text"] = polymerTup[2]
                dic["display"] = "none"
                dic["list"] = other_entitylist
                self.__other_data.append(dic)
            #
        #

    def __readNonPolymerData(self):
        elist = self.__cifObj.getValueList('pdbx_non_polymer_info')
        if not elist:
            return
        #
        nonpolymermap = {}
        colorList = []
        for d in elist:
            if ('instance_id' not in d) or ('residue_id' not in d) or ('linkage_info' not in d):
                continue
            #
            if ("highlight_with_color" in d) and (d["highlight_with_color"] == "Y"):
                if d['residue_id'] not in colorList:
                    colorList.append(d['residue_id'])
                #
            #
            if d['linkage_info'] == 'linked':
                self.__image_data.append((d['instance_id'], d['instance_id']))
            #
            if d['residue_id'] in nonpolymermap:
                nonpolymermap[d['residue_id']].append(d)
            else:
                list = []  # pylint: disable=redefined-builtin
                list.append(d)
                nonpolymermap[d['residue_id']] = list
            #
        #
        if not nonpolymermap:
            return
        #
        keylist = []
        for k, v in nonpolymermap.items():
            keylist.append(k)
        #
        keylist.sort()
        #
        action_nonpolymerlist = []
        other_nonpolymerlist = []
        for k in keylist:
            v = nonpolymermap[k]
            count = len(v)
            if k in colorList:
                text = '<span style="color:red;">' + k + "</span> (" + str(count) + " "
            else:
                text = k + ' (' + str(count) + ' '
            #
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
            #
            action_required = ''
            instlist = []
            for d in v:
                list_text += ' ' + d['instance_id']
                pdic = {}
                pdic['id'] = d['instance_id']
                pdic['linkage_info'] = d['linkage_info']
                if 'message' in d:
                    pdic['message'] = d['message']
                pdic['label'] = d['instance_id']
                pdic['focus'] = d['focus']
                instlist.append(pdic)
                #
                if ('action_required' in d) and (not action_required):
                    action_required = d['action_required']
                #
            #
            dic['list_text'] = list_text
            if instlist:
                dic['list'] = instlist
                dic['list_image_key'] = k
            #
            dic["arrow"] = "ui-icon-circle-arrow-e"
            dic["display"] = "none"
            other_nonpolymerlist.append(dic)
            #
            if action_required == "Y":
                act_dic = copy.deepcopy(dic)
                act_dic["arrow"] = "ui-icon-circle-arrow-s"
                act_dic["display"] = "block"
                action_nonpolymerlist.append(act_dic)
            #
        #
        if action_nonpolymerlist:
            dic = {}
            dic["id"] = "nonpolymers"
            dic["arrow"] = "ui-icon-circle-arrow-s"
            dic["text"] = "Non-polymers"
            dic["display"] = "block"
            dic["list"] = action_nonpolymerlist
            self.__action_required_data.append(dic)
        #
        if other_nonpolymerlist:
            dic = {}
            dic["id"] = "nonpolymers"
            dic["arrow"] = "ui-icon-circle-arrow-e"
            dic["text"] = "Non-polymers"
            dic["display"] = "none"
            dic["list"] = other_nonpolymerlist
            self.__other_data.append(dic)
        #

    def __readGroupData(self):
        elist = self.__cifObj.getValueList('pdbx_group_info')
        if not elist:
            return
        #
        action_grouplist = []
        other_grouplist = []
        for d in elist:
            if ('group_id' not in d) or ('descriptor' not in d) or ('residues' not in d) or ('linkage_info' not in d):
                continue
            #
            if d['linkage_info'] == 'linked':
                self.__image_data.append((d['group_id'], d['group_id'].upper()))
            #
            action_required = ''
            if 'action_required' in d:
                action_required = d['action_required']
            #
            dic = {}
            dic['id'] = 'g_' + d['group_id']
            dic['text'] = d['group_id'].upper() + ' (' + d['descriptor'] + ')'
            dic['list_text'] = 'Residues: ' + d['residues']
            instlist = []
            pdic = {}
            pdic['id'] = d['group_id']
            pdic['linkage_info'] = d['linkage_info']
            if 'message' in d:
                pdic['message'] = d['message']
            #
            pdic['label'] = d['group_id'].upper()
            pdic['focus'] = d['focus']
            instlist.append(pdic)
            dic['list'] = instlist
            #
            dic["arrow"] = "ui-icon-circle-arrow-e"
            dic["display"] = "none"
            other_grouplist.append(dic)
            #
            if action_required == "Y":
                act_dic = copy.deepcopy(dic)
                act_dic["arrow"] = "ui-icon-circle-arrow-s"
                act_dic["display"] = "block"
                action_grouplist.append(act_dic)
            #
        #
        if action_grouplist:
            dic = {}
            dic["id"] = "groups"
            dic["arrow"] = "ui-icon-circle-arrow-s"
            dic["text"] = "Connected residues(Groups)"
            dic["display"] = "block"
            dic["list"] = action_grouplist
            self.__action_required_data.append(dic)
        #
        if other_grouplist:
            dic = {}
            dic["id"] = "groups"
            dic["arrow"] = "ui-icon-circle-arrow-e"
            dic["text"] = "Connected residues(Groups)"
            dic["display"] = "none"
            dic["list"] = other_grouplist
            self.__other_data.append(dic)
        #

    def __readmatchResult(self):
        elist = self.__cifObj.getValueList('pdbx_match_result')
        if not elist:
            return
        #
        for d in elist:
            if 'inst_id' not in d:
                continue
            #
            if d['inst_id'].startswith('merge'):
                self.__combResidueFlag = True
            else:
                self.__matchResultFlag[d['inst_id']] = 'yes'
                #
                if 'method' in d and d['method'] == 'graph':
                    self.__graphmatchResultFlag = True
                #
            #
        #

    def __readSplitMergePolymerResidueResult(self):
        slist = self.__cifObj.getValueList('pdbx_split_polymer_residue_info')
        if slist:
            self.__splitPolymerResidueFlag = True
            for d in slist:
                if ('instance_id' not in d) or ('linkage_info' not in d):
                    continue
                #
                if d['linkage_info'] == 'linked':
                    self.__image_data.append((d['instance_id'], d['instance_id']))
                #
            #
        #
        mlist = self.__cifObj.getValueList('pdbx_merge_polymer_residue_info')
        if mlist:
            for d in mlist:
                if ('merge_id' not in d) or ('linkage_info' not in d):
                    continue
                #
                if d['linkage_info'] == 'linked':
                    self.__image_data.append((d['merge_id'], d['merge_id'].upper()))
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

    def __processingOneLetterSeq(self, input_seq, colorResMap):
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
        # return output_seq.replace('(', '<span style="color:red;">(').replace(')', ')</span>')
        for color, colorResList in colorResMap.items():
            for res in colorResList:
                output_seq = output_seq.replace("(" + res + ")", '<span style="color:' + color + ';">(' + res + ")</span>")
            #
        #
        return output_seq

    def __processingThreeLetterSeq(self, input_seq, colorResMap):
        output_seq = input_seq
        for color, colorResList in colorResMap.items():
            for res in colorResList:
                output_seq = output_seq.replace(res, '<span style="color:' + color + ';">' + res + "</span>")
            #
        #
        return output_seq
