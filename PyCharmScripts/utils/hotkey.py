import pymel.all as pm
HOTKEY_SET_NAME = 'nagi_hotkey'


def create():
    if not pm.hotkeySet(HOTKEY_SET_NAME, exists=True):
        pm.hotkeySet(HOTKEY_SET_NAME, source='Maya_Default')

    pm.hotkeySet(HOTKEY_SET_NAME, edit=True, current=True)
    pm.displayInfo("Set current hotkey set to {}".format(HOTKEY_SET_NAME))

    key = {'k': 'r', 'alt': True, 'ctl': False}
    empty_hotkey(**key)
    python_command = 'python("import PyCharmScripts.utils.attributes as attribute;reload(attribute);' \
                     'attribute.reset_attr(pm.selected(), custom_attr=False)")'
    command = pm.nameCommand('resetAttribute', command=python_command, ann='Reset Attribute Value')
    pm.hotkey(name=command, **key)
    pm.displayInfo("Set alt+r to reset transform")

    key = {'k': '!', 'alt': False, 'ctl': False}
    empty_hotkey(**key)
    python_command = 'python(\"pm.artAttrSkinPaintCtx(\'artAttrSkinContext\', e=True ,pickValue=True)\")'
    command = pm.nameCommand('pickSkinWeight', command=python_command, ann='Pick Skin Weight')
    pm.hotkey(name=command, **key)
    pm.displayInfo("Set ! for pick skin weight in paint skin weight tool")

    key = {'k': '4', 'alt': True, 'ctl': False}
    empty_hotkey(**key)
    python_command = 'python("import PyCharmScripts.utils.joints as joints;reload(joints);joints.show_joint();")'
    command = pm.nameCommand('showHideJoint', command=python_command, ann='Show and Hide Joints in viewport')
    pm.hotkey(name=command, **key)
    pm.displayInfo("Set alt+4 for show/ hide joints in viewport")


def empty_hotkey(**kargs):
    if pm.hotkeyCheck(**kargs):
        pm.hotkey(n='', rn='', **kargs)