##
# File:  ReadFormUtil.py
# Date:  30-Apr-2014
# Updates:
##
"""
Update PRD definition based on input form.

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
import traceback

from mmcif.io.PdbxReader import PdbxReader
from mmcif.api.DataCategory import DataCategory
from mmcif.io.PdbxWriter import PdbxWriter
#


class ReadFormUtil(object):
    """ Class responsible for updating PRD definition.

    """
    def __init__(self, reqObj=None, prdID=None, outputFile=None, verbose=False, log=sys.stderr):
        """
        """
        self.__verbose = verbose  # pylint: disable=unused-private-member
        self.__lfh = log
        self.__reqObj = reqObj
        self.__prdID = prdID
        self.__inputFile = str(self.__reqObj.getValue('prdfile'))
        self.__outputFile = outputFile
        self.__status = True
        #
        self.__readCif()

    def __readCif(self):
        """ Read input PRD file
        """
        self.__myBlock = None
        if not self.__inputFile or not os.access(self.__inputFile, os.F_OK):
            return
        #
        try:
            myDataList = []
            ifh = open(self.__inputFile, 'r')
            pRd = PdbxReader(ifh)
            pRd.read(myDataList)
            ifh.close()
            self.__myBlock = myDataList[0]
        except:  # noqa: E722  pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
        #

    def processForm(self):
        """ Process PRD input form and update PRD file
        """
        if not self.__myBlock:
            return False
        #
        self.__status = True
        self.__updateMolecule()
        self.__updateEntityList()
        self.__updateSourceInfo()
        self.__updatePolymerInfo()
        self.__updateLinkInfo()
        self.__updateDbrefInfo()
        self.__updateAuditInfo()
        self.__updatePrdID()
        self.__WriteCif()
        return self.__status

    def __updateMolecule(self):
        """ Update pdbx_reference_molecule category
        """
        itemMap = {}
        itemMap['name'] = 'mol_name'
        itemMap['type'] = 'type_id'
        itemMap['class'] = 'class_id'
        itemMap['release_status'] = 'release_status'
        itemMap['compound_details'] = 'comp_detail'
        itemMap['description'] = 'description'
        #
        myData = {}
        for key, val in itemMap.items():
            value = str(self.__reqObj.getValue(val))
            if value:
                myData[key] = value
            #
        #
        if not myData:
            return
        #
        cat = self.__myBlock.getObj('pdbx_reference_molecule')
        for key, val in myData.items():
            cat.setValue(val, key, 0)
        #

    def __updateEntityList(self):
        """ Update pdbx_reference_entity_list category
        """
        valMap = self.__getFormValue('detailid_', 1)
        if not valMap:
            return
        #
        cat = self.__myBlock.getObj('pdbx_reference_entity_list')
        for row in range(0, cat.getRowCount()):
            v = cat.getValue('component_id', row)
            if v in valMap:
                cat.setValue(valMap[v], 'details', row)
            #
        #

    def __getFormValue(self, pKey, num):
        """ Get form value
        """
        pmap = {}
        list = []  # pylint: disable=redefined-builtin
        list.append(pKey)
        valMap = self.__reqObj.getValueMap(list)
        if not valMap:
            return pmap
        #
        for key, val in valMap.items():
            list1 = key.split('_')
            if num == 2:
                idx = list1[1] + '_' + list1[2]
                pmap[idx] = val
            else:
                pmap[list1[1]] = val
            #
        #
        return pmap

    def __updateSourceInfo(self):
        """ Update pdbx_reference_entity_src_nat category
        """
        pKey_list = ['entityid_', 'orgsci_', 'taxid_', 'source_', 'sourceid_', 'natname_', 'natcode_']
        valMap = self.__reqObj.getValueMap(pKey_list)
        if not valMap:
            return
        #
        defined_row = self.__getSourceRow(valMap)
        if defined_row < 0:
            return
        #
        vlist = self.__getSourceList(defined_row, pKey_list, valMap)
        if not vlist:
            return
        #
        cat = self.__myBlock.getObj('pdbx_reference_entity_src_nat')
        if not cat:
            cat = DataCategory('pdbx_reference_entity_src_nat')
            cat.appendAttribute('prd_id')
            cat.appendAttribute('ref_entity_id')
            cat.appendAttribute('ordinal')
            cat.appendAttribute('taxid')
            cat.appendAttribute('organism_scientific')
            cat.appendAttribute('source')
            cat.appendAttribute('source_id')
            cat.appendAttribute('atcc')
            cat.appendAttribute('db_code')
            cat.appendAttribute('db_name')
            self.__myBlock.append(cat)
        #
        pmap = {}
        pmap['prd_id'] = 'prd_id'
        pmap['entityid_'] = 'ref_entity_id'
        pmap['orgsci_'] = 'organism_scientific'
        pmap['taxid_'] = 'taxid'
        pmap['source_'] = 'source'
        pmap['sourceid_'] = 'source_id'
        pmap['natcode_'] = 'db_code'
        pmap['natname_'] = 'db_name'
        #
        row = 0
        for sdir in vlist:
            cat.setValue(str(row + 1), 'ordinal', row)
            for token in ('prd_id', 'entityid_', 'orgsci_', 'taxid_', 'source_', 'sourceid_',
                          'natname_', 'natcode_'):
                if token in sdir:
                    cat.setValue(sdir[token], pmap[token], row)
            #
            row += 1
            #
        #

    def __getSourceRow(self, valMap):
        """ Get maximum source ID
        """
        defined_row = -1
        for key, _val in valMap.items():
            klist = key.split('_')
            n = int(str((klist[1])))
            if n > defined_row:
                defined_row = n
            #
        #
        return defined_row

    def __getSourceList(self, defined_row, pKey_list, valMap):
        """ Get values based on source ID
        """
        rlist = []
        for i in range(0, defined_row + 1):
            dir = {}  # pylint: disable=redefined-builtin
            for token in pKey_list:
                id = token + str(i)  # pylint: disable=redefined-builtin
                if id in valMap:
                    dir[token] = valMap[id]
                #
            #
            if 'orgsci_' in dir or 'taxid_' in dir or \
               'source_' in dir or 'sourceid_' in dir:
                dir['prd_id'] = self.__prdID
                rlist.append(dir)
            #
        #
        return rlist

    def __updatePolymerInfo(self):
        """ Update pdbx_reference_entity_poly_seq & pdbx_reference_entity_sequence categories
        """
        valMap = self.__getFormValue('polymerid_', 2)
        if not valMap:
            return
        #
        cat = self.__myBlock.getObj('pdbx_reference_entity_poly_seq')
        for row in range(0, cat.getRowCount()):
            v1 = cat.getValue('ref_entity_id', row)
            v2 = cat.getValue('num', row)
            key = v1 + '_' + v2
            if key in valMap:
                cat.setValue(valMap[key], 'parent_mon_id', row)
            #
        #
        one_letter_code_map = self.__getOneLetterCodeMap(cat)
        if not one_letter_code_map:
            return
        #
        seqCat = self.__myBlock.getObj('pdbx_reference_entity_sequence')
        for row in range(0, seqCat.getRowCount()):
            v1 = cat.getValue('ref_entity_id', row)
            if v1 in one_letter_code_map:
                seqCat.setValue(one_letter_code_map[v1], 'one_letter_codes', row)
            #
        #

    def __getOneLetterCodeMap(self, cat):
        """ Get one letter code sequence
        """
        aamap = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
                 "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
                 "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
                 "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}
        #
        one_letter_code_map = {}
        ref_entity_id = ''
        one_letter_code = ''
        for row in range(0, cat.getRowCount()):
            ref_id = cat.getValue('ref_entity_id', row)
            value = cat.getValue('parent_mon_id', row)
            if ref_id != ref_entity_id:
                if ref_entity_id and one_letter_code:
                    one_letter_code_map[ref_entity_id] = one_letter_code
                ref_entity_id = ref_id
                one_letter_code = ''
            if value in aamap:
                one_letter_code += aamap[value]
            else:
                one_letter_code += 'X'
            #
        #
        if ref_entity_id and one_letter_code:
            one_letter_code_map[ref_entity_id] = one_letter_code
        #
        return one_letter_code_map

    def __updateLinkInfo(self):
        """ Update pdbx_reference_entity_poly_link & pdbx_reference_entity_link categores
        """
        polylink = self.__getFormValue('polylink_', 1)
        polyatom1 = self.__getFormValue('polyatom1_', 1)
        polyatom2 = self.__getFormValue('polyatom2_', 1)
        entitylink = self.__getFormValue('entitylink_', 1)
        entityatom1 = self.__getFormValue('entityatom1_', 1)
        entityatom2 = self.__getFormValue('entityatom2_', 1)
        if polylink:
            self.__updateLinkCat('pdbx_reference_entity_poly_link', polylink, polyatom1, polyatom2)
        #
        if entitylink:
            self.__updateLinkCat('pdbx_reference_entity_link', entitylink, entityatom1, entityatom2)
        #

    def __updateLinkCat(self, catName, link, atom1, atom2):
        """ update linkage category
        """
        cat = self.__myBlock.getObj(catName)
        for row in range(0, cat.getRowCount()):
            v = cat.getValue('link_id', row)
            if v in link:
                cat.setValue(link[v], 'value_order', row)
            if v in atom1:
                cat.setValue(atom1[v], 'atom_id_1', row)
            if v in atom2:
                cat.setValue(atom2[v], 'atom_id_2', row)
            #
        #

    def __updateDbrefInfo(self):
        """ Update pdbx_reference_entity_poly category
        """
        dbname = self.__getFormValue('dbname_', 1)
        dbcode = self.__getFormValue('dbcode_', 1)
        if (not dbname) or (not dbcode):
            return
        #
        cat = self.__myBlock.getObj('pdbx_reference_entity_poly')
        for row in range(0, cat.getRowCount()):
            v = cat.getValue('ref_entity_id', row)
            if v in dbname and v in dbcode:
                cat.setValue(dbname[v], 'db_name', row)
                cat.setValue(dbcode[v], 'db_code', row)
            #
        #

    def __updateAuditInfo(self):
        """ Update pdbx_prd_audit category
        """
        actiontype = self.__getFormValue('actiontype_', 1)
        details = self.__getFormValue('auditdetails_', 1)
        if (not actiontype) and (not details):
            return
        #
        list = []  # pylint: disable=redefined-builtin
        uniqueMap = {}
        if actiontype:
            for k, _v in actiontype.items():
                uniqueMap[k] = 'yes'
                list.append(int(k))
            #
        #
        if details:
            for k, _v in details.items():
                if k in uniqueMap:
                    continue
                #
                list.append(int(k))
            #
        #
        list.sort()
        dlist = []
        for i in list:
            id = str(i)  # pylint: disable=redefined-builtin
            dir = {}  # pylint: disable=redefined-builtin
            if id in actiontype:
                dir['action_type'] = actiontype[id]
            #
            if id in details:
                dir['details'] = details[id]
            #
            dlist.append(dir)
        #
        cat = self.__myBlock.getObj('pdbx_prd_audit')
        row = 0
        for dir in dlist:
            for key, val in dir.items():
                cat.setValue(val, key, row)
            #
            row += 1
            #
        #

    def __updatePrdID(self):
        """ Update PRD ID
        """
        cat_list = ['pdbx_reference_molecule', 'pdbx_reference_entity_list', 'pdbx_reference_entity_nonpoly',
                    'pdbx_reference_entity_link', 'pdbx_reference_entity_poly_link', 'pdbx_reference_entity_poly',
                    'pdbx_reference_entity_sequence', 'pdbx_reference_entity_poly_seq', 'pdbx_reference_entity_src_nat',
                    'pdbx_prd_audit']
        #
        for category in cat_list:
            cat = self.__myBlock.getObj(category)
            if not cat:
                continue
            #
            for row in range(0, cat.getRowCount()):
                cat.setValue(self.__prdID, 'prd_id', row)
            #
        #
        self.__myBlock.setName(self.__prdID)

    def __WriteCif(self):
        """ Write out PRD file
        """
        try:
            myDataList = []
            ofh = open(self.__outputFile, 'w')
            myDataList.append(self.__myBlock)
            pdbxW = PdbxWriter(ofh)
            pdbxW.write(myDataList)
            ofh.close()
        except:  # noqa: E722  pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            self.__status = False
        #
