"""
Simple XML parser to handle Scope XML messages
"""

import xml.dom.minidom

def isScopeXml(str):
    try:
        dom = xml.dom.minidom.parseString(str)
    except xml.parsers.expat.ExpatError:
        print "[Exception] Bad XML format."
        return False
        
    if dom.documentElement.tagName == 'scope_job':
        return True
    elif dom.documentElement.tagName == 'scope_config':
        file = open("../config/scope_config.xml", "wb")
        dom.writexml(file)
        file.close()
        return True
    else:
        return False