import json
import os

import pymel.all as pm

import colors
from PyCharmScripts.utils import channels
from PyCharmScripts.data import name_data
from PyCharmScripts.utils import common

reload(common)
reload(colors)
reload(channels)
reload(name_data)

folder_path = os.path.abspath(__file__).split('main.py')[0]
file_loc = folder_path + "prefab.json"
thumbnail_path = folder_path + "thumbnails\\"

# TODO: make support multiple shapes creation


def read_prefab():
    with open(file_loc) as rf:
        shp_dict = json.load(rf)
    return shp_dict


def append_prefab(obj, name=''):
    old_obj = obj
    if not name:
        dialog = pm.promptDialog(t='Add to Library', m='Curve Name:', tx=obj.name(), b=['OK', 'Cancel'], cb='Cancel')
        if dialog == 'OK':
            name = pm.promptDialog(q=1, tx=1)
            new_obj = pm.duplicate(obj, name=name, rr=1)[0]
            obj = new_obj
            old_obj.v.set(0)
        else:
            return
        # name = obj.name()

    shp_dict = {}
    if os.stat(file_loc).st_size != 0:
        with open(file_loc) as rf:
            shp_dict = json.load(rf)

    if name in shp_dict.keys():
        dialog = pm.confirmDialog(t='Warning', m="{} is already exists in library. Overwrite it?".format(name),
                                  b=['OK', 'Cancel'], cb='Cancel', db='ok')
        if dialog != 'OK':
            return

    pt_list = obj.getCVs()
    cv_pos = []
    degree = obj.degree()
    for pt in pt_list:
        cv_pos.append([pt.x, pt.y, pt.z])
    new_dict = {name: {'degree': degree, 'cv': cv_pos, 'knots': obj.getKnots()}}

    shp_dict.update(new_dict)
    # print shp_dict
    with open(file_loc, "w") as write_file:
        json.dump(shp_dict, write_file, indent=4)

    create_thumbnail([obj])

    pm.delete(obj)
    old_obj.v.set(1)

    return shp_dict


def create(shp_name, name='', groups=['nul'], color=None, create_all=False, text='', const_pxy=False):

    shp_dict = read_prefab()

    with pm.UndoChunk():
        if create_all:
            con_list = []
            for key in shp_dict.keys():
                con_data = shp_dict[key]
                con = pm.curve(name=key, p=con_data['cv'], d=con_data['degree'], k=con_data['knots'])
                con_list.append(con)
            return con_list

        if text:
            shp_transform = pm.PyNode(pm.textCurves(t=text, ch=0, font='arial')[0])
            pm.makeIdentity(shp_transform, apply=1, t=1)
            con = pm.createNode('transform', name=name)
            pm.parent(shp_transform.getChildren(ad=1, type='nurbsCurve'), con, r=1, s=1)
            pm.delete(shp_transform)

            for i, shp in enumerate(con.getShapes()):
                shp.rename(con + 'Shape{}'.format(i + 1))
                if i > 0:
                    shp.isHistoricallyInteresting.set(0)

            pm.xform(con, cp=1)
            pm.move(0, 0, 0, con, rpr=1)
            pm.makeIdentity(con, apply=1, t=1)
        else:
            if shp_name not in shp_dict.keys():
                print "{} not exist in prefab.".format(shp_name)
                return
            con_data = shp_dict[shp_name]
            con = pm.curve(name=name, p=con_data['cv'], d=con_data['degree'], k=con_data['knots'])

        if const_pxy:
            pxy_grp = common.group_pivot(con, layer=['const_pxy'])[0]
            pm.parent(con, w=1)
            for at in 'trs':
                con.attr(at).connect(pxy_grp.attr(at))

        if isinstance(color, int):
            colors.override_shape([con], color=color)
        elif isinstance(color, basestring):
            colors.override_shape([con], side=color)

        if groups:
            # grps = []
            # for grp in groups:
            #     temp = pm.group(name='{}_{}_')
            grps = common.group_pivot(con, layer=groups)
            if const_pxy:
                con.getParent().addChild(pxy_grp)
                grps.append(pxy_grp)
            grps.append(con)
            return grps
        return con


def create_sub_ctrl(objs, scale=.8):
    output = []
    for obj in objs:
        if 'subCtrlVis' not in pm.listAttr(obj, ud=1):
            obj.addAttr('subCtrlVis', at='double', min=0, max=1, k=1, dv=0)

        new_objs = pm.duplicate(obj, name=common.replace_name(obj.name(), 'ctrl', 'sub_{}'.format(
            name_data.TYPE_LIST['ctrl'])))[0]
        output.append(new_objs)
        for nobj in new_objs.getChildren(ad=1):
            if nobj not in new_objs.getShapes():
                pm.delete(nobj)
            else:
                obj.subCtrlVis.connect(nobj.visibility)
        new_objs.s.set([.8] * 3)
        pm.makeIdentity(new_objs, a=1)
        obj.addChild(new_objs)
    return output


def swap_curve(source, targets, keep_source=True):
    """
    Swap curves
    :param source:
    :param targets:
    :param keep_source:
    :return:
    """
    if isinstance(targets, pm.PyNode):
        targets = [targets]

    for target in targets:
        dul_src = pm.duplicate(source, rr=1, rc=1)[0]
        # pm.matchTransform(dul_src, target)
        target.addChild(dul_src)
        dul_src.t.set([0] * 3)
        dul_src.r.set([0] * 3)
        dul_src.s.set([1] * 3)
        pm.makeIdentity(dul_src, apply=True, translate=True, rotate=True, scale=True)

        # shape attributes
        argv = colors.get_override_data(target.getShapes(ni=1)[0])
        colors.override_shape([dul_src], **argv)

        pm.delete(target.getShapes(ni=1))
        pm.parent(dul_src.getShapes(ni=1), target, r=1, s=1)
        for i, shp in enumerate(target.getShapes(ni=1)):
            shp.rename("{}Shape{}".format(target, i))

        pm.delete(dul_src)

    if not keep_source:
        pm.delete(source)


def add_pivot_ctrl(obj, con_scale=1):
    """
    add pivot control
    :param obj:
    :param con_scale:
    :return:
    """
    parent = obj.getParent()
    pxy_obj = obj
    # create proxy and parent original obj under it
    # ori_name = obj.name()
    #
    # obj.rename("{}_const".format(ori_name))
    # pxy_obj = pm.duplicate(obj, po=1, name=ori_name)[0]
    # for at in obj.listAttr(ud=1):
    #     if at.isConnectable():
    #         try:
    #             pxy_obj.attr(at.attrName()).connect(at)
    #         except Exception as e:
    #             print e
    #             continue
    # pm.parent(obj.getShapes(), pxy_obj, r=1, s=1)
    # pxy_obj.addChild(obj)

    piv_ctrl = create('locator', name="{}_piv".format(obj), groups=[], color=24)
    pxy_obj.addAttr('pivot_ctrl', at='double', min=0, max=1, k=1, dv=0)
    pxy_obj.pivot_ctrl.connect(piv_ctrl.v)
    piv_ctrl.s.set([con_scale] * 3)
    pm.makeIdentity(piv_ctrl, a=1, s=1)

    pm.matchTransform(piv_ctrl, pxy_obj, pos=1, rot=0)

    piv_ctrl.t.connect(pxy_obj.rotatePivot)
    piv_ctrl.t.connect(pxy_obj.scalePivot)
    parent.addChild(piv_ctrl)

    channels.cb_status(piv_ctrl, rotates='xyz', scales='xyz', v=1, lock=1, show=0)

    return piv_ctrl


def add_group(objs, key, suffix):
    """
    add group on top of objs
    :param key:
    :param objs:
    :param suffix: suffix of group
    :return:
    """
    grps = []
    for obj in objs:
        new_name = common.replace_name(obj.name(), key, suffix)
        if new_name == obj.name():
            print new_name, obj.name()
            new_name = '{}_{}'.format(obj, suffix)
        new_grp = common.group_pivot(obj, layer=['temp'], world=False)[0]
        new_grp.rename(new_name)
        grps.append(new_grp)
    return grps


def create_thumbnail(objs):
    pb_argvs = {'clearCache': True,
                'compression': 'png',
                'endTime': 1,
                'forceOverwrite': True,
                'format': 'image',
                'framePadding': 0,
                'offScreen': True,
                'percent': 100,
                'quality': 100,
                'showOrnaments': False,
                'startTime': 1,
                'viewer': False,
                'widthHeight': (250, 250)}

    for obj in objs:
        obj.v.set(0)

    pm.select(cl=1)
    for obj in objs:
        obj.v.set(1)
        pm.select(obj)
        pm.viewFit()
        pm.select(cl=1)
        # pm.isolateSelect(panel, state=1)

        colors.override_shape(obj, color='white')

        pb_argvs['filename'] = os.path.join(thumbnail_path, obj.name())
        pm.playblast(**pb_argvs)
        print '--create thumbnail for {}--'.format(obj)
        obj.v.set(0)
        colors.override_shape(obj, disable=True)
    for obj in objs:
        obj.v.set(1)


def create_chain(objs, shape='circle', groups=['nul'], color=None, replace_key=['joint', 'ctrl'], con_scale=[1, 1, 1]):
    """
    create a chain of controllers
    :param con_scale: scale of controller
    :param objs:
    :param shape:
    :param groups:
    :param color:
    :param replace_key:
    :return:
    """
    cons = []
    for obj in objs:
        new_name = common.replace_name(obj.name(), replace_key[0], replace_key[1])

        con_dict = create(shape, name=new_name, groups=groups, color=color)
        pm.matchTransform(con_dict[0], obj)

        if con_scale:
            con_dict[-1].s.set(con_scale)
            pm.makeIdentity(con_dict[-1], s=1, a=1)

        if cons:
            cons[-1][-1].addChild(con_dict[0])
        cons.append(con_dict)
    return cons
