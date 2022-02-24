##
# File:  DepictPrd.py
# Date:  23-Apr-2014
# Updates:
##
"""
Create HTML depiction for PRD entry.

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

from wwpdb.apps.entity_transform.prd.DepictUtil import DepictUtil
from wwpdb.apps.entity_transform.prd.HtmlUtil import HtmlUtil
from wwpdb.apps.entity_transform.utils.CommandUtil import CommandUtil
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
#


class DepictPrd(object):
    """ Class responsible for generating HTML depiction of PRD entry.
    """
    def __init__(self, reqObj=None, prdID=None, prdFile=None, myD=None, verbose=False, log=sys.stderr):
        if myD is None:
            myD = {}
        self.__verbose = verbose
        self.__lfh = log
        self.__reqObj = reqObj
        self.__prdID = prdID  # pylint: disable=unused-private-member
        self.__prdFile = prdFile
        self.__myD = myD
        self.__sObj = None
        self.__sessionId = None
        self.__sessionPath = None
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__dictRoot = self.__cICommon.get_mmcif_dict_path()
        self.__dictionary_v5 = self.__cICommon.get_mmcif_archive_next_dict_filename() + '.odb'
        #
        self.__depictUtil = None
        self.__htmlUtil = None
        self.__prdObj = None
        #
        self.__getSession()
        #

    def getDepictContext(self):
        """
        """
        self.__getPrdObject()
        self.__initialSetting()
        #
        self.__depictUtil = DepictUtil()
        self.__htmlUtil = HtmlUtil()
        #
        # Meta data info
        #
        self.__getTextualData()
        self.__getClassInfo()
        self.__getTypeInfo()
        self.__getStatusInfo()
        #
        # Component info
        #
        self.__getComponentList()
        #
        # Source info
        #
        self.__getSourceInfo()
        #
        # Polymer info
        #
        self.__getPolymerInfo()
        self.__myD['polylink'] = self.__getLinkInfo('pdbx_reference_entity_poly_link')
        #
        # Other info
        #
        self.__myD['entitylink'] = self.__getLinkInfo('pdbx_reference_entity_link')
        self.__getDbrefInfo()
        self.__getAuditInfo()
        #
        return self.__myD

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self.__sObj = self.__reqObj.newSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        if (self.__verbose):
            self.__lfh.write("------------------------------------------------------\n")
            self.__lfh.write("+DepictPrd.__getSession() - creating/joining session %s\n" % self.__sessionId)
            self.__lfh.write("+DepictPrd.__getSession() - session path %s\n" % self.__sessionPath)

    def __getPrdObject(self):
        """ Read built PRD cif file
        """
        self.__prdObj = None
        if not os.access(self.__prdFile, os.F_OK):
            return
        #
        self.__prdObj = mmCIFUtil(filePath=self.__prdFile)

    def __getTextInfo(self, cat, item):
        """ Get textual value from PRD object
        """
        if not self.__prdObj:
            return ''
        #
        return self.__prdObj.GetSingleValue(cat, item)

    def __getCategoryInfo(self, category):
        """ Get category values from PRD object
        """
        if not self.__prdObj:
            return []
        #
        return self.__prdObj.GetValue(category)

    def __getEntityList(self, include_default, polymer_only):
        """ Get entity list from pdbx_reference_entity_list category
        """
        entity_list = []
        if include_default:
            entity_list.append('')
            entity_list.append('.')
        #
        elist = self.__getCategoryInfo('pdbx_reference_entity_list')
        if elist:
            dir = {}  # pylint: disable=redefined-builtin
            for d in elist:
                if polymer_only:
                    type = ''  # pylint: disable=redefined-builtin
                    if 'type' in d:
                        type = d['type']
                    #
                    if (not type) or (type != 'polymer'):
                        continue
                    #
                #
                if 'ref_entity_id' not in d:
                    continue
                #
                if d['ref_entity_id'] in dir:
                    continue
                #
                dir[d['ref_entity_id']] = 'yes'
                entity_list.append(d['ref_entity_id'])
            #
        #
        return entity_list

    def __initialSetting(self):
        """
        """
        for item in ('sessionid', 'identifier', 'pdbid', 'instanceid', 'label', 'annotator', 'site'):
            self.__myD[item] = str(self.__reqObj.getValue(item))
        #
        self.__myD['prdcc_button'] = '&nbsp;'
        self.__myD['single_comment_start'] = '<!--'
        self.__myD['single_comment_end'] = '-->'
        self.__myD['comp_detail_flag_start'] = ''
        self.__myD['comp_detail_flag_end'] = ''
        represent_type = self.__getTextInfo('pdbx_reference_molecule', 'represent_as').lower()
        if represent_type == 'polymer':
            # self.__myD['prdcc_button'] = '<input type="submit" name="submit" value="Download PRDCC" />'
            self.__myD['single_comment_start'] = ''
            self.__myD['single_comment_end'] = ''
            self.__myD['comp_detail_flag_start'] = self.__myD['update_comment_start']
            self.__myD['comp_detail_flag_end'] = self.__myD['update_comment_end']
        #

    def __getTextualData(self):
        """ Get molecule name, component details & description
        """
        # fmt: off
        lists = [['mol_name',    'name',             'style_background_color1'],  # noqa: E241
                 ['comp_detail', 'compound_details', 'style_background_color2'],
                 ['description', 'description',      'style_background_color3']]  # noqa: E241
        # fmt: on
        for list in lists:  # pylint: disable=redefined-builtin
            self.__myD[list[0]] = self.__getTextInfo('pdbx_reference_molecule', list[1])
            self.__myD[list[2]] = 'style = "background-color:#D3D6FF;"'
            if self.__myD[list[0]]:
                self.__myD[list[2]] = ''
            #
        #

    def __getClassInfo(self):
        """ Get _pdbx_reference_molecule.class value from PRD object
        """
        enumList = self.__getEnumList('_pdbx_reference_molecule.class')
        text = self.__getTextInfo('pdbx_reference_molecule', 'class')
        self.__myD['class'] = self.__htmlUtil.addSelect('class_id', text, enumList)

    def __getTypeInfo(self):
        """ Get _pdbx_reference_molecule.type value from PRD object
        """
        enumList = self.__getEnumList('_pdbx_reference_molecule.type')
        text = self.__getTextInfo('pdbx_reference_molecule', 'type')
        self.__myD['type'] = self.__htmlUtil.addSelect('type_id', text, enumList)

    def __getStatusInfo(self):
        """ Get _pdbx_reference_molecule.release_status value from PRD object
        """
        enumList = self.__getEnumList('_pdbx_reference_molecule.release_status')
        text = self.__getTextInfo('pdbx_reference_molecule', 'release_status')
        self.__myD['status'] = self.__htmlUtil.addSelect('release_status_id', text, enumList)

    def __getComponentList(self):
        """ Get pdbx_reference_entity_list values from PRD object
        """
        dlist = self.__getCategoryInfo('pdbx_reference_entity_list')
        self.__myD['component_list'] = self.__depictUtil.DepictComponentList(dlist)

    def __getSourceInfo(self):
        """ Depict pdbx_reference_entity_src_nat values
        """
        entity_list = self.__getEntityList(True, False)
        slist = self.__getCategoryInfo('pdbx_reference_entity_src_nat')
        row = len(slist) + 5
        self.__myD['sourcerow'] = str(row)
        self.__myD['source'] = self.__depictUtil.DepictSourceInfo(slist, row, entity_list)

    def __getPolymerInfo(self):
        """ Get pdbx_reference_entity_poly_seq values from PRD object
        """
        aalist = ['', '?', 'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS',
                  'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL']
        #
        dlist = self.__getCategoryInfo('pdbx_reference_entity_poly_seq')
        self.__myD['polymer'] = self.__depictUtil.DepictPolymerInfo(dlist, aalist)

    def __getLinkInfo(self, category):
        """ Get pdbx_reference_entity_poly_link/pdbx_reference_entity_link values from PRD object
        """
        text = ''
        dlist = self.__getCategoryInfo(category)
        if not dlist:
            return text
        #
        missing_residue = self.__getMissingResidues()
        #
        return self.__depictUtil.DepictLinkInfo(category, dlist, missing_residue)

    def __getDbrefInfo(self):
        """ Depict DBREF info
        """
        entityList = self.__getEntityList(False, True)
        if not entityList:
            self.__myD['dbref'] = ''
            return
        #
        dbinfo = self.__getRefData()
        #
        self.__myD['dbref'] = self.__depictUtil.DepictDbrefInfo(entityList, dbinfo)

    def __getAuditInfo(self):
        """ Get pdbx_prd_audit values from PRD object
        """
        dlist = self.__getCategoryInfo('pdbx_prd_audit')
        if not dlist:
            self.__myD['detail'] = ''
            return
        #
        enumList = self.__getEnumList('_pdbx_prd_audit.action_type')
        #
        self.__myD['detail'] = self.__depictUtil.DepictAuditInfo(dlist, enumList)

    def __getEnumList(self, item):
        """ Get enumeration list from from cif dictionary
        """
        enumList = []
        #
        cmdUtil = CommandUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
        rootName = cmdUtil.getRootFileName('Enum')
        cmdUtil.runAnnotCmd('GetEnumValue', os.path.join(self.__dictRoot, self.__dictionary_v5), rootName + '.txt',
                            rootName + '.log', '', ' -item ' + item)
        #
        filepath = os.path.join(self.__sessionPath, rootName + '.txt')
        if not os.access(filepath, os.F_OK):
            return enumList
        #
        f = open(filepath, 'r')
        data = f.read()
        f.close()
        #
        enumList = data.split('\n')
        enumList.sort()
        return enumList

    def __getMissingResidues(self):
        """ Get missing residues
        """
        missing_residue = {}
        polymer = self.__getCategoryInfo('pdbx_reference_entity_poly_seq')
        if not polymer:
            return missing_residue
        #
        item_list = ['ref_entity_id', 'num', 'mon_id']
        #
        for d in polymer:
            observed = ''
            if 'observed' in d:
                observed = d['observed']
            if observed != 'N':
                continue
            #
            v_list = []
            for item in item_list:
                v = ''
                if item in d:
                    v = d[item]
                #
                v_list.append(v)
            #
            idx = '_'.join(v_list)
            missing_residue[idx] = 'Y'
        #
        return missing_residue

    def __getRefData(self):
        """ Read DB reference Info from pdbx_reference_entity_poly category
        """
        dir = {}  # pylint: disable=redefined-builtin
        dlist = self.__getCategoryInfo('pdbx_reference_entity_poly')
        if not dlist:
            return dir
        #
        for d in dlist:
            ref_id = ''
            if 'ref_entity_id' in d:
                ref_id = d['ref_entity_id']
            #
            if not ref_id:
                continue
            dir1 = {}
            if 'db_name' in d:
                dir1['db_name'] = d['db_name']
            #
            if 'db_code' in d:
                dir1['db_code'] = d['db_code']
            #
            if dir1:
                dir[ref_id] = dir1
            #
        #
        return dir
