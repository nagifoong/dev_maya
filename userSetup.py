import sys

import maya.OpenMaya as om
import maya.cmds as cmds
import pymel.all as pm

pathList = [r'D:\PyCharmProjects\dev_maya']
for p in pathList:
    if p not in sys.path:
        sys.path.append(p)
    else:
        print "{} already in script path env.".format(p)

from PyCharmScripts.shelves import shelf_toolbelt
reload(shelf_toolbelt)

cmds.evalDeferred("shelf_toolbelt.clear_shelves();shelf_toolbelt.ToolBeltShelf()")


def aSave(n):
    if cmds.file(q=1,uc=1):
        cmds.delete('uiConfigurationScriptNode')
        cmds.file(s=1,uc=0)
kSave = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterSave, aSave)

### mop ##
# import sys

# sys.dont_write_bytecode = True
# print 'importing mop'
# cmds.evalDeferred("import thirdParty.mop as mop; mop.ui.menu; mop.ui.menu.build_menu()")

