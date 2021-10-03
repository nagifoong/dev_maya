import pymel.all as pm

from PyCharmScripts.utils import ui_utils
from PyCharmScripts.data import color_data

reload(color_data)
reload(ui_utils)

COLOR_DICT = color_data.COLOR_DICT

SIDE_COLOR = color_data.SIDE_COLOR

displayDict = {'normal': 0, 'template': 1, 'reference': 2}


def override_shape(objs, side='', disable=False, color='', display_type='normal'):
    """
    Set override color on object shapes
    :param objs: objects
    :param side: side of the object
    :param disable:
    :param color:
    :param display_type:
    :return:
    """
    if isinstance(objs, pm.PyNode):
        objs = [objs]

    with pm.UndoChunk():
        for obj in objs:
            if not isinstance(obj, pm.PyNode):
                obj = pm.PyNode(obj)
            if not obj.getShapes():
                print "# {} has no shapes under it. Skipped it.".format(obj.name())
                continue
            for shp in obj.getShapes():
                # override enable
                if shp.overrideEnabled.isConnected() or shp.overrideEnabled.isLocked():
                    print "Unable to change on override on {}".format(shp)
                    continue

                if disable:
                    shp.overrideEnabled.set(0)
                else:
                    shp.overrideEnabled.set(1)

                # override color
                if color or side:
                    if shp.overrideColor.isConnected() or shp.overrideColor.isLocked():
                        print "Unable to override color on {}".format(shp)
                    else:
                        if side:
                            shp.overrideColor.set(COLOR_DICT[SIDE_COLOR[side]])
                        else:
                            color_val = COLOR_DICT[color] if isinstance(color, basestring) else color
                            shp.overrideColor.set(color_val)

                # display type
                if display_type:
                    if shp.overrideDisplayType.isConnected() or shp.overrideDisplayType.isLocked():
                        print "Unable to override display type on {}".format(shp)
                    else:
                        shp.overrideDisplayType.set(displayDict[display_type])

    return


def get_override_data(obj):
    """get override data for set data"""
    data = {'disable': False if obj.overrideEnabled.get() else True, 'color': obj.overrideColor.get()}
    display_type = obj.overrideDisplayType.get()
    for dt in displayDict.keys():
        if display_type == displayDict[dt]:
            data['display_type'] = dt
            break
    return data
