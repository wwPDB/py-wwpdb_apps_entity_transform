##
# File:  StrFormDepict.py
# Date:  02-Dec-2012
# Updates:
##
"""
Create HTML depiction for various merge/split scenarios

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

from wwpdb.apps.entity_transform.depict.DepictBase import DepictBase
from wwpdb.apps.entity_transform.depict.SeqDepict import SeqDepict
from wwpdb.apps.entity_transform.update.CombineCoord import CombineCoord
from wwpdb.utils.config.ConfigInfo import ConfigInfo
#


class StrFormDepict(DepictBase):
    """ Class responsible for generating HTML depiction of various merge/split scenarios.
    """
    def __init__(self, reqObj=None, summaryCifObj=None, verbose=False, log=sys.stderr):
        super(StrFormDepict, self).__init__(reqObj=reqObj, summaryCifObj=summaryCifObj, verbose=verbose, log=log)
        #
        self.__siteId = str(self._reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI = ConfigInfo(self.__siteId)
        #
        self.__submitValue = str(self._reqObj.getValue('submit'))
        self.__entityList = self._reqObj.getValueList('entity')
        self.__chainList = self._reqObj.getValueList('chain')
        self.__ligandList = self._reqObj.getValueList('ligand')
        self.__groupList = []
        self.__entity_info = {}
        self.__entity_chain_mapping = {}
        self.__chain_entity_mapping = {}

    def LaunchFixer(self):
        template = ''
        myD = {}
        myD['pdbid'] = self._pdbId
        myD['sessionid'] = self._sessionId
        myD['identifier'] = self._identifier
        myD['title'] = ''
        if self._cifObj:
            myD['title'] = self._cifObj.getTitle()
        #
        if self.__submitValue == 'Split with chopper':
            template, myD = self.__processSplitWithChopper(myD)
        else:
            self.__getGroupList()
            self.__readEntityData()
            #
            if self.__submitValue == 'Merge to polymer':
                template, myD = self.__processMergePolymer(myD)
            elif self.__submitValue == 'Split polymer to polymer(s)/non-polymer(s)':
                template, myD = self.__processSplitPolymer(myD)
            elif self.__submitValue == 'Remove residue(s) from polymer sequence(s)':
                template, myD = self.__processEditPolymerSequence(myD)
            elif self.__submitValue == 'Merge/Split with chopper':
                template, myD = self.__processMergeSplit(myD)
            elif self.__submitValue == 'Merge to ligand':
                template, myD = self.__processMergeLigand(myD)
            #
        #
        if template:
            return self._processTemplate(template, myD)
        else:
            return ''
        #

    def LaunchEditor(self):
        myD = {}
        myD['pdbid'] = self._pdbId
        myD['identifier'] = self._identifier
        myD['sessionid'] = self._sessionId
        myD['instanceid'] = str(self._reqObj.getValue('instanceid'))
        myD['label'] = str(self._reqObj.getValue('label'))
        myD['related_instanceids'] = ''
        myD['annotator'] = ''
        if os.access(os.path.join(self._sessionPath, "annotator_initial"), os.F_OK):
            f = open(os.path.join(self._sessionPath, "annotator_initial"), "rb")
            myD['annotator'] = f.read()
            if sys.version_info[0] > 2:
                myD['annotator'] = myD['annotator'].decode('ascii')
            f.close()
        #
        myD['session_url_prefix'] = os.path.join(self._rltvSessionPath, 'search', myD['instanceid'])
        myD['processing_site'] = self.__cI.get('SITE_NAME').upper()
        #
        return self._processTemplate('chopper/editor_tmplt.html', myD)

    def __processSplitWithChopper(self, myD):
        ciffile = self._identifier + '_model_P1.cif'
        residueId = str(self._reqObj.getValue('split_polymer_residue'))
        if not residueId:
            residueId = '_'.join([str(self._reqObj.getValue('chain_id')), str(self._reqObj.getValue('res_name')),
                                  str(self._reqObj.getValue('res_num')), str(self._reqObj.getValue('ins_code'))])
        #
        combObj = CombineCoord(reqObj=self._reqObj, instList=[residueId], cifFile=ciffile, verbose=self._verbose, log=self._lfh)
        combObj.processWithCopy(submitValue=self.__submitValue)
        message = combObj.getMessage()
        #
        if message:
            myD['data'] = message
            return 'update_form/update_result_tmplt.html', myD
        #
        instId = combObj.getInstId()
        myD['instanceid'] = instId
        myD['comp'] = os.path.join(self._rltvSessionPath, instId, instId + '.comp.cif')
        myD['button'] = self._processTemplate('chopper/button_tmplt.html', {'value' : 'Split', 'option' : 'split_residue'})
        myD['processing_site'] = self.__cI.get('SITE_NAME').upper()
        return 'chopper/chopper_tmplt.html', myD

    def __getGroupList(self):
        group_list = self._reqObj.getValueList('group')
        if group_list:
            for v in group_list:
                list1 = str(v).split(',')
                self.__groupList.append(','.join(list1[1:]))
            #
        #

    def __readEntityData(self):
        if not self._cifObj:
            return
        #
        dlist = self._cifObj.getValueList('entity_poly')
        if not dlist:
            return
        #
        for d in dlist:
            if 'entity_id' not in d:
                continue
            #
            dic = {}
            for item in ('entity_id', 'pdbx_strand_id', 'name', 'type', 'pdbx_seq_one_letter_code', 'pdbx_seq_coord_align_label'):
                if item in d:
                    dic[item] = d[item]
                #
            #
            if not dic:
                continue
            #
            self.__entity_info[dic['entity_id']] = dic
            #
            if 'pdbx_strand_id' in dic:
                chain_list = dic['pdbx_strand_id'].split(',')
                self.__entity_chain_mapping[dic['entity_id']] = chain_list
                for c in chain_list:
                    self.__chain_entity_mapping[c] = dic['entity_id']
                #
            #
        #

    def __processMergePolymer(self, myD):
        html_text = '<span style="font-weight:bold; font-size:16px">\n'
        groups = self.__getGroups()
        if len(groups) > 1:
            html_text += 'Merging following user defined groups to polymers:\n'
            html_text += '</span>\n<br/> <br/>\n'
            count = 1
            for group in groups:
                html_text += '<br/>User Defined Group ' + str(count) + ': <br/>\n'
                html_text += self.__processMergeGroup(group, str(count))
                count += 1
            #
        else:
            html_text += 'Merging following user defined group to polymer:<br/>\n'
            html_text += '</span>\n<br/> <br/>\n'
            html_text += self.__processMergeGroup(groups[0], '1')
        #
        myD['form_data'] = html_text
        return 'update_form/merge_polymer_tmplt.html', myD

    def __processSplitPolymer(self, myD):
        entities = self.__getSelectedEntitiesInfo()
        #
        jscript = ''
        html_text = 'No entity found.'
        if entities:
            seqObj = SeqDepict(entityInfo=entities, option="split", verbose=self._verbose, log=self._lfh)
            html_text = seqObj.getHtmlText()
            jscript = seqObj.getScriptText()
        #
        myD['script'] = jscript
        myD['form_data'] = html_text
        return 'update_form/split_polymer_tmplt.html', myD

    def __processEditPolymerSequence(self, myD):
        entities = self.__getSelectedEntitiesInfo()
        #
        jscript = ''
        html_text = 'No entity found.'
        if entities:
            seqObj = SeqDepict(entityInfo=entities, option="edit", verbose=self._verbose, log=self._lfh)
            html_text = seqObj.getHtmlText()
            jscript = seqObj.getScriptText()
        #
        myD['script'] = jscript
        myD['form_data'] = html_text
        return 'update_form/edit_polymer_sequence_tmplt.html', myD

    def __processMergeSplit(self, myD):
        instlist = []
        self.__getList(self.__chainList, instlist)
        self.__getList(self.__ligandList, instlist)
        self.__getList(self.__groupList, instlist)
        ciffile = self._identifier + '_model_P1.cif'
        combObj = CombineCoord(reqObj=self._reqObj, instList=instlist, cifFile=ciffile, verbose=self._verbose, log=self._lfh)
        combObj.processWithCombine()
        message = combObj.getMessage()
        #
        if message:
            myD['data'] = message
            return 'update_form/update_result_tmplt.html', myD
        #
        instId = combObj.getInstId()
        myD['instanceid'] = instId
        myD['comp'] = os.path.join(self._rltvSessionPath, instId, instId + '.comp.cif')
        myD['button'] = self._processTemplate('chopper/button_tmplt.html', {'value' : 'Merge to Ligand', 'option' : 'merge'}) \
            + self._processTemplate('chopper/button_tmplt.html', {'value' : 'Split to Polymer', 'option' : 'split'})
        myD['processing_site'] = self.__cI.get('SITE_NAME').upper()
        return 'chopper/chopper_tmplt.html', myD

    def __processMergeLigand(self, myD):
        html_text = '<span style="font-weight:bold; font-size:16px">\n'
        groups = self.__getGroups()
        if len(groups) > 1:
            html_text += 'Merging following user defined groups to ligands:\n'
            html_text += '</span>\n<br/> <br/>\n'
            count = 1
            for group in groups:
                html_text += '<br/>User Defined Group ' + str(count) + ': <br/>\n'
                html_text += self.__processMergeGroup(group, str(count), polymer=False)
                count += 1
            #
        else:
            html_text += 'Merging following user defined group to ligand:<br/>\n'
            html_text += '</span>\n<br/> <br/>\n'
            html_text += self.__processMergeGroup(groups[0], '1', polymer=False)
        #
        myD['form_data'] = html_text
        return 'update_form/merge_ligand_tmplt.html', myD

    def __getGroups(self):
        dic = {}
        group_id = []
        #
        self.__processGroup('chain_', self.__chainList, dic, group_id)
        self.__processGroup('ligand_', self.__ligandList, dic, group_id)
        self.__processGroup('group_', self.__groupList, dic, group_id)
        #
        group_id.sort()
        groups = []
        for v in group_id:
            groups.append(dic[v])
        #
        return groups

    def __processGroup(self, token, valueList, dic, group_id):
        if not valueList:
            return
        #
        for v in valueList:
            name = token + str(v)
            value = str(self._reqObj.getValue(name))
            if not value:
                value = '-'
            #
            if token != 'group_':
                self.__addToGroup(name, value, dic, group_id)
            else:
                tlist = str(v).split(',')
                for val in tlist:
                    list1 = val.split('_')
                    if len(list1) == 1:
                        name = 'chain_' + val
                    else:
                        name = 'ligand_' + val
                    self.__addToGroup(name, value, dic, group_id)
                #
            #
        #

    def __addToGroup(self, name, value, dic, group_id):
        if value in dic:
            for v in dic[value]:
                if v == name:
                    return
                #
            #
            dic[value].append(name)
        else:
            tlist = []
            tlist.append(name)
            dic[value] = tlist
            group_id.append(value)
        #

    def __processMergeGroup(self, group, group_id, polymer=True):
        enum = []
        for i in range(0, len(group)):
            enum.append(str(i + 1))
        #
        count = 1
        text = ''
        new_ligand_id = ''
        for v in group:
            tlist = v.split('_')
            token = tlist[0]
            value = tlist[1]
            label = token
            if token == 'ligand':
                label = 'residue'
                value = '_'.join(tlist[1:])
                if not new_ligand_id:
                    new_ligand_id = tlist[2]
                #
            #
            text += '<input type="hidden" name="' + token + '" value="' + value + '" />'
            text += '<input type="hidden" name="group_' + value + '" value="' + group_id + '" />'
            text += label + ' ' + value + ' &nbsp; '
            if polymer:
                text += self.__selectTag('order_' + value, str(count), enum) + ' &nbsp; &nbsp; &nbsp; '
            else:
                text += ' &nbsp; <input type="hidden" name="order_' + value + '" value="' + str(count) + '" />'
            #
            count += 1
        #
        if not polymer:
            text += ' &nbsp; &nbsp; New Residue Name: &nbsp; &nbsp; <input type="text" size="10" name="group_id_' + group_id + '" value="' + new_ligand_id + '" />'
        #
        text += ' <br/>\n'
        return text

    def __getSelectedEntitiesInfo(self):
        entities = []
        _included_chainIDs = {}
        #
        if self.__entityList:
            for v in self.__entityList:
                entity_id = str(v)
                chainids = ''
                if entity_id in self.__entity_chain_mapping:
                    chainids = ','.join(self.__entity_chain_mapping[entity_id])
                    for c in self.__entity_chain_mapping[entity_id]:
                        _included_chainIDs[c] = 'yes'
                    #
                #
                self.__addSelectedEntitiesInfo(entities, entity_id, chainids)
            #
        #
        if self.__chainList:
            for v in self.__chainList:
                chain_id = str(v)
                if chain_id in _included_chainIDs:
                    continue
                #
                _included_chainIDs[chain_id] = 'yes'
                if chain_id not in self.__chain_entity_mapping:
                    continue
                #
                self.__addSelectedEntitiesInfo(entities, self.__chain_entity_mapping[chain_id], chain_id)
                #
            #
        #
        return entities

    def __addSelectedEntitiesInfo(self, entities, entity_id, chainids):
        if entities:
            for e_list in entities:
                if e_list[0] == entity_id:
                    e_list[1] = e_list[1] + ',' + chainids
                    return
                #
            #
        #
        if entity_id not in self.__entity_info:
            return
        #
        if 'pdbx_seq_one_letter_code' not in self.__entity_info[entity_id]:
            return
        #
        tlist = []
        # tlist[0]: entity ID
        tlist.append(entity_id)
        # tlist[1]: chain IDs
        tlist.append(chainids)
        # tlist[2]: molecule name
        if 'name' in self.__entity_info[entity_id]:
            tlist.append(self.__entity_info[entity_id]['name'])
        else:
            tlist.append('')
        # tlist[3]: one letter code sequence
        tlist.append(self.__entity_info[entity_id]['pdbx_seq_one_letter_code'])
        # tlist[4]: polymer type
        if 'type' in self.__entity_info[entity_id]:
            tlist.append(self.__entity_info[entity_id]['type'])
        else:
            tlist.append('')
        # tlist[5]: seq/coords alignment label string: 001111... (0 = no coord aligned, 1 = has coord(s) aligned)
        if 'pdbx_seq_coord_align_label' in self.__entity_info[entity_id]:
            tlist.append(self.__entity_info[entity_id]['pdbx_seq_coord_align_label'])
        else:
            tlist.append('')
        #
        entities.append(tlist)

    def __selectTag(self, name, value, enum):
        text = '<select name="' + name + '">\n'
        for v in enum:
            text += '<option value="' + v + '" '
            if v == value:
                text += 'selected'
            # text += '> <span style="font-size:20px;font-weight:bold">' + v + '</span> \n'
            text += '> ' + v + '\n'
            #
        text += '</select>\n'
        return text

    def __getList(self, valueList, groups):
        if not valueList:
            return
        #
        for v in valueList:
            val = str(v)
            list1 = val.split(',')
            if len(list1) == 1:
                self.__addToList(val, groups)
            else:
                for val1 in list1:
                    self.__addToList(val1, groups)
                #
            #
        #

    def __addToList(self, val, groups):
        if groups:
            for v in groups:
                if v == val:
                    return
                #
            #
        #
        groups.append(val)
