import pymel.all as pm
HOTKEY_SET_NAME = 'nagi_hotkey'


def create():
    if not pm.hotkeySet(HOTKEY_SET_NAME, exists=True):
        pm.hotkeySet(HOTKEY_SET_NAME, source='Maya_Default')

    pm.hotkeySet(HOTKEY_SET_NAME, edit=True, current=True)
    pm.displayInfo("Set current hotkey set to {}".format(HOTKEY_SET_NAME))

    key = {'k': 'r', 'alt': True, 'ctl': False}
    python_command = """for obj in pm.selected():
    for at in 'trs':
        for ax in 'xyz':
            try:
                obj.attr(at + ax).set(0 if at != 's' else 1)
            except (Exception, ):
                print 'Unable to reset {}.{}'.format(obj, at+ax)"""
    create_hotkey(cmd_name='resetAttribute', command=python_command, annotation='Reset Attribute Value', **key)
    pm.displayInfo("Set alt+r to reset transform")

    key = {'k': '!', 'alt': False, 'ctl': False}
    python_command = 'artAttrPaintOperation artAttrSkinPaintCtx Replace;artAttrSkinPaintCtx -edit -pickValue ' \
                     '"artAttrSkinContext"; '
    create_hotkey(cmd_name='PickSkinWeight', command=python_command, annotation='Pick Skin Weight', **key)
    pm.displayInfo("Set ! for pick skin weight in paint skin weight tool")

    key = {'k': '4', 'alt': True, 'ctl': False}
    empty_hotkey(**key)
    python_command = """editors = [q for q in pm.lsUI(p=1) if q.type() == 'modelEditor']
status = pm.modelEditor(editors[0].split('|')[-1], q=1, j=1)
for ed in editors:
    name = ed.split('|')[-1]
    pm.modelEditor(name, e=1, j=False if status else True)"""
    create_hotkey(cmd_name='showHideJoint', command=python_command, annotation='Show and Hide Joints in viewport', **key)
    pm.displayInfo("Set alt+4 for show/ hide joints in viewport")

    key = {'k': 'g', 'alt': True, 'ctl': False}
    python_command = r"""import pymel.all as pm
import maya.mel as mel
active = 'Add'
for item in pm.lsUI(type='radioButton'):
    if 'artAttrSkin' in item.name() and 'OperRadio' in item.name() and item.getSelect():
        active = item.getLabel()
        break
mel.eval('artAttrPaintOperation artAttrSkinPaintCtx Smooth;')
for i in range(10):
    mel.eval("FloodSurfaces")
mel.eval('artAttrPaintOperation artAttrSkinPaintCtx {};'.format(active))
"""
    create_hotkey(cmd_name='SmoothWeight10x', command=python_command, annotation='Smooth skin weight 10x', **key)
    pm.displayInfo("Set alt+g for smooth skin weight 10x")


def empty_hotkey(**kargs):
    if pm.hotkeyCheck(**kargs):
        pm.hotkey(n='', rn='', **kargs)


def create_hotkey(cmd_name='temp', command='', annotation='', **kargs):
    empty_hotkey(**kargs)
    if not pm.runTimeCommand(cmd_name, query=True, exists=True):
        pm.runTimeCommand(cmd_name, category='Custom Scripts')
    pm.runTimeCommand(cmd_name, edit=True, command=command,
                      ann=annotation, category='Custom Scripts')
    cmd = pm.nameCommand('{}Command'.format(cmd_name), command=cmd_name, ann=annotation)
    pm.hotkey(name=cmd, **kargs)
