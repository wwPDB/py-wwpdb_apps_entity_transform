##
# File:  HtmlUtil.py
# Date:  28-Apr-2014
# Updates:
##
"""
HTML Utility Class

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


class HtmlUtil(object):
    def addSelect(self, name, value, enum):
        """ Write HTML section tag
        """
        background = 'style = "background-color:#D3D6FF;"'
        if value:
            for v in enum:
                if v == value:
                    background = ''
                    break
                #
            #
        #
        text = '<select ' + background + ' name="' + name + '">\n'
        for v in enum:
            text += '<option value="' + v + '" '
            if v == value:
                text += 'selected'
            text += ' /> <span style="font-size:20px;font-weight:bold">' + v + '</span> \n'
            #
        text += '</select>\n'
        return text

    def addInput(self, type, name, value, checked, display):  # pylint: disable=redefined-builtin
        """ Write HTML input tag with various options
        """
        text = '<input type="' + type + '" name="' + name + '" value="' \
            + value + '" ' + checked + ' /> ' + display + ' \n'
        if type == 'text' and not value:
            text = '<input style = "background-color:#D3D6FF;" type="' + type + '" name="' + name \
                + '" value="' + value + '" ' + checked + ' /> ' + display + ' \n'
        return text

    def addText(self, name, value, size):
        """ Write HTML input text tag with size attribute
        """
        text = '<input style = "background-color:#00FF99;" type="text" name="' + name + \
               '" value="' + value + '" ' + size + ' /> \n'
        return text

    def addTD(self, value):
        """ Write HTML td tag
        """
        return '<td style="text-align:left;border-style:none">' + value + '</td>\n'

    def addColorTD(self, value, color):
        """ Write HTML td tag with background color
        """
        if value:
            return '<td style="text-align:left;border-style:none;background-color:' + color + '">' + value + '</td>\n'
        else:
            return '<td style="text-align:left;border-style:none"></td>\n'
        #

    def addSpanTD(self, colspan, value):
        """ Write HTML td tag with colspan attribute
        """
        return '<td style="text-align:left;border-style:none" colspan="' + colspan + '">' + value + '</td>\n'

    def addTR(self, value):
        """ Write HTML tr tag
        """
        return '<tr>' + value + '</tr>\n'

    def getSize(self, default, value):
        """ Get size attribute
        """
        size = default
        if len(value) > size:
            size = len(value) + 1
        #
        return 'size="' + str(size) + '"'
