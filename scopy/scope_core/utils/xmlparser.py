"""
Simple XML parser to handle Scope XML messages
"""

from lxml import etree
from scope_core.config import settings

def isScopeXml(str):
    try:
        dom = etree.fromstring(str)
    except etree.XMLSyntaxError:
        print "[Exception] Bad XML format."
        return False
        
    if dom.tag == 'scope_job':
        return True
    elif dom.tag == 'scope_config':
        file = open(settings.CONFIG_PATH, "w")
        file.write(etree.tostring(dom, pretty_print=True, xml_declaration=True, encoding='utf-8'))
        file.close()
        return True
    else:
        return False