import pymel.all as pm
import maya.OpenMaya as om
import maya.mel as mel

# from PyCharmScripts.utils.common import create_name, create_matrix_constrain
import common
import skinning
import joints
import channels
from PyCharmScripts.tools.controllerShape import main as shape_gen

reload(common)
reload(skinning)
reload(joints)
reload(channels)
reload(shape_gen)

create_name = common.create_name
create_matrix_constrain = common.create_matrix_constrain


def get_even_surface_param(surf, count=5, axis='u', from_zero=True):
    if isinstance(surf, basestring):
        if pm.ls(surf):
            surf = pm.PyNode(surf)

    if not surf.getShapes(ni=1, type='nurbsSurface'):
        print 'Given object, {}, does not contain nurbsSurface.'.format(surf)
        return

    result = []
    surf_shp = surf.getShapes(ni=1, type='nurbsSurface')[0]

    crv = pm.createNode('nurbsCurve')
    surf_to_crv = pm.createNode('curveFromSurfaceIso')
    surf_shp.worldSpace.connect(surf_to_crv.inputSurface)
    surf_to_crv.outputCurve.connect(crv.create)
    surf_to_crv.relativeValue.set(1)
    surf_to_crv.isoparmValue.set(.5)
    if axis == 'u':
        surf_to_crv.isoparmDirection.set(0)
    else:
        surf_to_crv.isoparmDirection.set(1)

    if from_zero:
        diff = 1.0 / (count - 1)
    else:
        diff = 1.0 / (count + 1)

    for n in range(count):
        val = crv.findParamFromLength(crv.length() * diff * n)

        if axis == 'u':
            result.append([val, .5])
        else:
            result.append([.5, val])

    pm.delete(crv, surf_to_crv)
    return result


def create_obj_on_surface(surf, num=5, from_zero=True, axis='v', shp_scale=1, source=None, new_name='',
                          auto_prefix=False, rot=True, param_only=False):
    """
    create objs(num) and attach to nurbs surface. Only nurbsSurface (ribbon)
    :param param_only: return position list only
    :param rot: constraint rotate
    :param surf:
    :param num:
    :param from_zero:
    :param axis: "u" or "v"
    :param shp_scale
    :param source: create obj based on provided [position(s)]
    :param new_name: new name to replace surface name
    :param auto_prefix: give generated object with prefix "l", "r" and "m"
    :return:
    """
    if source is None:
        source = []

    if isinstance(surf, basestring):
        if pm.ls(surf):
            surf = pm.PyNode(surf)

    if not surf.getShapes(ni=1, type='nurbsSurface'):
        print 'Given object, {}, does not contain nurbsSurface.'.format(surf)
        return

    if source:
        num = len(source)

    if from_zero:
        diff = 1.0 / (num - 1)
        val = 0
    else:
        diff = 1.0 / (num + 1)
        val = diff

    loc_list = []
    suffix = len(str(num))
    surf_shp = surf.getShapes(ni=1, type='nurbsSurface')[0]

    crv = ''
    neg_dict = {}
    pos_dict = {}
    mid_dict = {}
    surf_to_crv = None
    # param_list = []

    if not source:
        crv = pm.createNode('nurbsCurve')
        surf_to_crv = pm.createNode('curveFromSurfaceIso')
        surf_shp.worldSpace.connect(surf_to_crv.inputSurface)
        surf_to_crv.outputCurve.connect(crv.create)
        surf_to_crv.relativeValue.set(1)
        surf_to_crv.isoparmValue.set(.5)
        if axis == 'u':
            surf_to_crv.isoparmDirection.set(0)
        else:
            surf_to_crv.isoparmDirection.set(1)

    # create group for cons
    loc_grp_name = create_name(side='', name=new_name, fn='loc', _type='group')
    if not pm.ls(loc_grp_name):
        loc_grp = pm.group(name=loc_grp_name, em=1)
    else:
        loc_grp = pm.PyNode(loc_grp_name)

    for n in range(num):
        num_suffix = str(n + 1).zfill(suffix)

        # create locator
        loc_name = create_name(side='', name=surf, fn=num_suffix, _type='locator')
        loc_struc = shape_gen.create('locator', name=loc_name, groups=['nul', 'offset'])
        loc_grp.addChild(loc_struc[0])
        loc_list.append(loc_struc[-1])

        # add attribute on grp
        loc_struc[0].addAttr('paramU', at='double', k=1)
        loc_struc[0].addAttr('paramV', at='double', k=1)

        # scale con shape size
        loc_list[-1].s.set([shp_scale] * 3)
        pm.makeIdentity(loc_list[-1], a=1, s=1)

        posi = create_name(side='', name=surf, fn=num_suffix, _type='pointOnSurfaceInfo', create=True)
        loc_struc[0].paramU.connect(posi.u)
        loc_struc[0].paramV.connect(posi.v)

        # if source is provided
        if source:
            try:
                pnt = surf.closestPoint(source[n])[0]
                param = surf.getParamAtPoint(pnt)
            except Exception as e:
                e = e
                om_sel = om.MSelectionList()
                om_sel.add(surf_shp.name())
                d_path = om.MDagPath()
                om_sel.getDagPath(0, d_path)
                m_surf = om.MFnNurbsSurface(d_path)
                rest = m_surf.closestPoint(om.MPoint(source[n][0], source[n][1], source[n][2]))

                u_util = om.MScriptUtil()
                u_util.createFromDouble(0)
                u_param = u_util.asDoublePtr()

                v_util = om.MScriptUtil()
                v_util.createFromDouble(0)
                v_param = v_util.asDoublePtr()
                m_surf.getParamAtPoint(rest, u_param, v_param, False, om.MSpace.kWorld)
                param = (round(om.MScriptUtil.getDouble(u_param), 3), round(om.MScriptUtil.getDouble(v_param), 3))

        else:
            val = crv.findParamFromLength(crv.length() * diff * n)

            # posi.top.set(True)
            if axis == 'u':
                param = [val, .5]
            else:
                param = [.5, val]

        loc_struc[0].paramU.set(param[0])
        loc_struc[0].paramV.set(param[1])
        surf_shp.worldSpace.connect(posi.inputSurface)

        # four by four matrix
        four_by_four = create_name(side='', name=surf, fn=num_suffix, _type='fourByFourMatrix', create=True)
        for i, at in enumerate(['nu', 'nn', 'nv', 'p']):
            for j, ax in enumerate('xyz'):
                # if at == 'tu':
                #     vec_prod.attr('o' + ax).connect(four_by_four.attr('in{}{}'.format(i, j)))
                #     continue
                posi.attr(at + ax).connect(four_by_four.attr('in{}{}'.format(i, j)))

        # decompose Matrix
        dcmp = create_name(side='', name=surf, fn=num_suffix, _type='decomposeMatrix', create=True)
        four_by_four.output.connect(dcmp.inputMatrix)
        dcmp.outputTranslate.connect(loc_struc[0].t)
        if rot:
            dcmp.outputRotate.connect(loc_struc[0].r)
        else:
            pass
            # loc_struc[0].r.set(dcmp.outputRotate.get())
        # dcmp.outputScale.connect(loc_struc[0].s)

        # separate for naming
        if auto_prefix:
            x_pos = round(pm.xform(loc_struc[0], q=1, ws=1, t=1)[0], 3)
            replace_key = create_name(side='', name=surf, fn='{}'.format(num_suffix), _type='')

            if x_pos == 0:
                mid_dict[loc_struc[0]] = (replace_key, create_name(side='middle', name=new_name, _type=''))
            elif x_pos > 0:
                pos_dict[loc_struc[0]] = (replace_key, create_name(side='left', name=new_name, _type=''))
            elif x_pos < 0:
                neg_dict[loc_struc[0]] = (replace_key, create_name(side='right', name=new_name, _type=''))

        val += diff

    # rename
    if auto_prefix:
        # sort middle by y position
        # change round argument to tweak mid tolerance
        mid_list = sorted(mid_dict, key=lambda obj: round(pm.xform(obj, q=1, ws=1, t=1)[1], 1))
        # sort left and right by x position
        pos_list = sorted(pos_dict, key=lambda obj: round(pm.xform(obj, q=1, ws=1, t=1)[0], 3))
        neg_list = sorted(neg_dict, key=lambda obj: round(pm.xform(obj, q=1, ws=1, t=1)[0], 3), reverse=True)
        sort_list = [mid_list, pos_list, neg_list]

        for i, objs in enumerate([mid_dict, pos_dict, neg_dict]):
            for ind, key in enumerate(sort_list[i]):
                if len(objs.keys()) == 1:
                    argv_str = '"{}" "{}"'.format(objs[key][0], objs[key][1])
                else:
                    argv_str = '"{}" "{}_{}"'.format(objs[key][0], objs[key][1],
                                                     str(ind + 1).zfill(len(str(len(sort_list[i]) + 1))))
                # print argv_str, sort_list[i]
                mel.eval('searchReplaceNames {} "all";'.format(argv_str))

    # sort locs
    sorted_locs = sorted(loc_grp.getChildren())
    pm.parent(sorted_locs, w=1)
    pm.parent(sorted_locs, loc_grp)

    # clean up
    if not source:
        pm.delete(crv.getParent(), surf_to_crv)

    return {'main_grp': loc_grp, 'locs': loc_list}


aimVs = {'l': {'x': [1, 0, 0], 'y': [0, 1, 0], 'z': [0, 0, 1]},
         'r': {'x': [-1, 0, 0], 'y': [0, -1, 0], 'z': [0, 0, -1]}}
upVs = {'l': {'x': [0, 0, 1], 'y': [1, 0, 0], 'z': [1, 0, 0]},
        'r': {'x': [0, 0, -1], 'y': [-1, 0, 0], 'z': [-1, 0, 0]}}
suffixKeys = {0: 'start', 1: 'mid', 2: 'end'}


def create_bendy(joint_list=None, prefix="ribbon", side='l', forward='x', up='z', con_scale=1, joint_count=5,
                 mirror=False):
    """
    create ribbon with providing exact two joints in joint list.
    up axis will dictate the loft normals. Suggested z always pointed at world z-axis
    V2, not using bezier curve but constraint weights to mimic bezier curve behavior
    :param joint_count: amount of joint to be created
    :param mirror: mirror behavior of the controllers
    :param up: up axis
    :param joint_list: [list], accept two joints only
    :param prefix:
    :param side:
    :param forward: forward axis
    :param con_scale: scale of cons
    :return:
    """
    if joint_list is None:
        # joint_list = []
        print 'provided joint invalid'
        return

    full_name = "{}_{}".format(side, prefix)

    '''make sure side is either "l" or "r"'''
    if side.lower() not in 'lr':
        # l is with normal forward and up axis
        side = 'l'

    con_dict = {}
    surf_jnts = []
    jnts = []

    rad = joint_list[0].radius.get() / 2.0
    rot = 'r' + forward
    trns = 't' + forward

    # check 1st joint parent
    prnt = joint_list[0].getParent()
    if not prnt:
        prnt = create_name(side='', name=joint_list[0], fn='ofs', _type='group', create=True)
        pm.delete(pm.parentConstraint(joint_list[0], prnt))
        prnt.addChild(joint_list[0])
        print "==BENDY== Missing parent for \"{}\". Please constrain \"{}\" for correct behavior.".format(joint_list[0], prnt)

    '''main groups'''
    main_nul_grp = create_name(side='', name=full_name, fn='bendy_ofs', _type='group', create=True)
    pm.delete(pm.parentConstraint(joint_list[0], main_nul_grp))
    pm.parentConstraint(prnt, main_nul_grp, mo=1)
    pm.scaleConstraint(prnt, main_nul_grp, mo=1)

    main_con_grp = create_name(side='', name=full_name, fn='bendy_con', _type='group', create=True)
    main_nul_grp.addChild(main_con_grp)
    pm.parentConstraint(joint_list[0], main_con_grp)

    main_util_grp = create_name(side='', name=full_name, fn='bendy_util', _type='group', create=True)
    global_scale = create_name(side='', name=full_name, fn='global_scale', _type='group', create=True)
    main_util_grp.addChild(global_scale)
    pm.scaleConstraint(prnt, global_scale)

    # Add attributes
    main_grp = main_nul_grp
    # main_grp.addAttr('disableBend', min=0, max=1, dv=0, k=1, at='double')
    main_grp.addAttr('autoTwist', min=0, max=1, dv=1, k=1, at='double')
    main_grp.addAttr('bendUpDown', k=1, at='double')
    main_grp.addAttr('bendFrontBack', k=1, at='double')
    main_grp.addAttr('twistStart', k=1, at='double')
    main_grp.addAttr('twistEnd', k=1, at='double')
    main_grp.addAttr('twistStartEnable', k=1, at='double', min=0, max=1, dv=1)
    main_grp.addAttr('twistEndEnable', k=1, at='double', min=0, max=1, dv=1)
    main_grp.addAttr('twistStartRotateOrder', k=1, at='enum', en='xyz:yzx:zxy:xzy:yxz:zyx')
    main_grp.twistStartRotateOrder.set(3, k=0, cb=1)
    main_grp.addAttr('twistEndRotateOrder', k=1, at='enum', en='xyz:yzx:zxy:xzy:yxz:zyx')
    main_grp.twistEndRotateOrder.set(3, k=0, cb=1)
    main_grp.addAttr('squash', min=0, max=1, dv=1, k=1, at='double')
    main_grp.addAttr('volume', min=0, dv=1, k=1, at='double')

    # disable twistStart and twistEnd value
    auto_node = create_name(side='', name=full_name, fn='autoTwist', _type='multiplyDivide', create=True)
    main_grp.twistStart.connect(auto_node.input1X)
    main_grp.twistEnd.connect(auto_node.input1Z)
    main_grp.autoTwist.connect(auto_node.input2X)
    main_grp.autoTwist.connect(auto_node.input2Z)

    # negate twist from group
    neg_node = create_name(side='', name=full_name, fn='negateParent', _type='plusMinusAverage', create=True)
    neg_node.operation.set(2 if side == 'l' else 1)

    auto_node.outputX.connect(neg_node.input3D[0].input3Dx)
    auto_node.outputZ.connect(neg_node.input3D[0].input3Dz)
    main_con_grp.attr(rot).connect(neg_node.input3D[1].input3Dx)

    end_neg_rev = create_name(side='', name=full_name, fn='end_negate', _type='reverse', create=True)
    main_grp.twistEndEnable.connect(end_neg_rev.inputX)

    end_neg_mult = create_name(side='', name=full_name, fn='end_negate', _type='multiplyDivide', create=True)
    main_con_grp.attr(rot).connect(end_neg_mult.i1x)
    end_neg_rev.outputX.connect(end_neg_mult.i2x)
    end_neg_mult.outputX.connect(neg_node.input3D[1].input3Dz)

    '''create bezier curve'''
    st_jnt, ed_jnt = joint_list
    st_pos = pm.xform(st_jnt, q=1, ws=1, t=1)
    ed_pos = pm.xform(ed_jnt, q=1, ws=1, t=1)
    pos_list = [st_pos]
    diff_pos = (ed_pos[0] - st_pos[0]) / 4.0, (ed_pos[1] - st_pos[1]) / 4.0, (ed_pos[2] - st_pos[2]) / 4.0
    for q in range(1, 5):
        pos_list.append((pos_list[-1][0] + diff_pos[0], pos_list[-1][1] + diff_pos[1], pos_list[-1][2] + diff_pos[2]))

    name = create_name(side='', name=full_name, _type='curve')
    b_crv = pm.curve(name=name, bezier=1, p=pos_list)

    '''create tangent controllers and attributes'''
    suffix_ind = 0
    ite = 1
    tangent_clamp = ''
    for ind, pos in enumerate(pos_list):
        # get suffix name
        suffix = suffixKeys[suffix_ind]

        # create joint and locator for surface
        pm.select(cl=1)
        jnt = create_name(side='', name=full_name, fn='temp_surf', _type='joint', create=True)
        jnt.radius.set(rad)
        surf_jnts.append(jnt)
        loc = create_name(side='', name=full_name, fn='temp', _type='locator', create=True)
        loc.addChild(jnt)
        loc.v.set(0, l=1)

        name = create_name(side='', name=full_name, fn='temp', _type='ctrl')
        con_grp, drv_grp, con = shape_gen.create('dumbbell', name=name, groups=['offset', 'driven'], color=18)

        if ind % 2 == 0:
            con.s.set([con_scale, con_scale, con_scale])
        else:
            con.s.set([con_scale * .8, con_scale * .8, con_scale * .8])
        pm.makeIdentity(con, apply=1, s=1)

        con.addChild(loc)
        con_grp.t.set(pos)
        con_grp.r.set(pm.xform(main_grp, q=1, ws=1, ro=1))
        loc.worldPosition.connect(b_crv.controlPoints[ind])

        if mirror:
            drv_grp.attr('r' + forward).set(180)
            drv_grp.attr('s' + forward).set(-1)

        temp_list = [con_grp, drv_grp, con, loc, jnt]
        if ind % 2 == 0:

            if ind == 2:
                con.addAttr('tangentConVis', at='double', min=0, max=1, dv=0, k=1)
                con.addAttr('tangentOffset', at='double', min=0, max=1, dv=.5, k=1)
                # tangent_rev = create_name(side='', name=full_name, fn='tangentOffset', _type='reverse', create=True)
                # con.tangentOffset.connect(tangent_rev.inputX)
                # tangent_clamp = create_name(side='', name=full_name, fn='tangentOffset', _type='clamp', create=True)
                # tangent_clamp.min.set([.001] * 3)
                # tangent_clamp.max.set([.999] * 3)
                # tangent_rev.inputX.connect(tangent_clamp.inputR)
                # tangent_rev.outputX.connect(tangent_clamp.inputB)

            suffix_ind += 1

            for obj in temp_list:
                obj.rename(obj.replace('temp', "{}".format(suffix)))

            con_dict[suffix] = [[], temp_list]

        elif ind == 1:
            for obj in temp_list:
                obj.rename(obj.replace('temp', "midA"))
            con_dict['between'] = [temp_list]

        elif ind == 3:
            for obj in temp_list:
                obj.rename(obj.replace('temp', "midB"))
            con_dict['between'].append(temp_list)

        # lock attributes
        channels.cb_status(con, scales='xyz', v=1, lock=1, show=0)
        ite += 1

    front = 'xyz'.replace(up, '').replace(forward, '')
    front_at = 't' + front
    up_dn_uc = create_name(side='', name=full_name, fn='bendUpDown', _type='unitConversion', create=True)
    up_dn_uc.conversionFactor.set(-1 if side == 'r' else 1)
    main_grp.bendUpDown.connect(up_dn_uc.input)
    up_dn_uc.output.connect(con_dict['mid'][1][1].attr('t' + up))

    fnt_bk_uc = create_name(side='', name=full_name, fn='bendFrontBack', _type='unitConversion', create=True)
    fnt_bk_uc.conversionFactor.set(-1 if side == 'r' else 1)
    main_grp.bendFrontBack.connect(fnt_bk_uc.input)
    fnt_bk_uc.output.connect(con_dict['mid'][1][1].attr(front_at))

    # constraint start and end controller groups to joint_list
    pm.pointConstraint(joint_list[0], con_dict['start'][1][0], mo=1)
    pm.pointConstraint(joint_list[1], con_dict['end'][1][0], mo=1)

    # constraint mid controller
    pm.pointConstraint(con_dict['start'][1][-1], con_dict['end'][1][-1], con_dict['mid'][1][0])
    pm.aimConstraint(con_dict['end'][1][-1], con_dict['mid'][1][0], aimVector=aimVs[side][forward],
                     upVector=upVs[side][forward], worldUpType='objectrotation', worldUpObject=con_dict['start'][1][2],
                     worldUpVector=upVs[side][forward])

    # twist attribute
    con_dict['start'][1][2].addAttr('twist', at='double', dv=0, k=1)
    con_dict['end'][1][2].addAttr('twist', at='double', dv=0, k=1)

    # '''grouping for disabling bendy'''
    # mid_sub_a_const_grp = create_name(side='', name="{}_midA".format(full_name), fn='constraint',
    #                                   _type='group', create=True)
    # mid_sub_b_const_grp = create_name(side='', name="{}_midB".format(full_name), fn='constraint',
    #                                   _type='group', create=True)
    # mid_const_grp = create_name(side='', name="{}_mid".format(full_name), fn='constraint', _type='group', create=True)
    #
    # pm.parent(mid_const_grp, mid_sub_a_const_grp, mid_sub_b_const_grp, con_dict['mid'][1][0])
    # pm.delete(pm.parentConstraint(con_dict['mid'][1][2], mid_const_grp))

    pm.parent(con_dict['between'][0][0], con_dict['between'][1][0], con_dict['mid'][1][2])
    # aim constraint for mid objects
    # ptc_a = pm.pointConstraint(con_dict['start'][1][-1], con_dict['mid'][1][-1], con_dict['between'][0][1], mo=0)
    # # pm.aimConstraint(con_dict['mid'][1][-1], con_dict['between'][0][0], aimVector=aimVs[side][forward],
    # #                  upVector=upVs[side][forward], worldUpType='object', worldUpObject=con_dict['start'][1][2])
    # #
    # ptc_b = pm.pointConstraint(con_dict['mid'][1][-1], con_dict['end'][1][-1], con_dict['between'][1][1], mo=0)
    # # pm.aimConstraint(con_dict['end'][1][-1], con_dict['between'][1][0], aimVector=aimVs[side][forward],
    # #                  upVector=upVs[side][forward], worldUpType='object', worldUpObject=con_dict['end'][1][2])
    #
    # tangent_clamp.outputR.connect(ptc_a.getWeightAliasList()[1])
    # tangent_clamp.outputR.connect(ptc_b.getWeightAliasList()[0])
    # tangent_clamp.outputB.connect(ptc_a.getWeightAliasList()[0])
    # tangent_clamp.outputB.connect(ptc_b.getWeightAliasList()[1])
    #
    # con_dict['mid'][1][2].tangentOffset.set(1)
    # a_min = con_dict['between'][0][1].attr(trns).get()
    # b_min = con_dict['between'][1][1].attr(trns).get()
    #
    # con_dict['mid'][1][2].tangentOffset.set(0)
    # a_max = con_dict['between'][0][1].attr(trns).get()
    # b_max = con_dict['between'][1][1].attr(trns).get()
    #
    # con_dict['mid'][1][2].tangentOffset.set(0.5)
    # create remap value
    remap_a = create_name(side='', name=full_name, fn='A_tangentOffset', _type='remapValue', create=True)
    remap_a.outputMin.set(con_dict['between'][0][0].attr(trns).get() * -.999)
    remap_a.outputMax.set(con_dict['between'][0][0].attr(trns).get() * .999)
    con_dict['mid'][1][2].tangentOffset.connect(remap_a.inputValue)
    remap_a.outValue.connect(con_dict['between'][0][1].attr(trns), f=1)

    remap_b = create_name(side='', name=full_name, fn='B_tangentOffset', _type='remapValue', create=True)
    remap_b.outputMin.set(con_dict['between'][1][0].attr(trns).get() * -.999)
    remap_b.outputMax.set(con_dict['between'][1][0].attr(trns).get() * .999)
    con_dict['mid'][1][2].tangentOffset.connect(remap_b.inputValue)
    remap_b.outValue.connect(con_dict['between'][1][1].attr(trns), f=1)
    #
    # tangent_clamp.outputR.connect(con_dict['between'][0][1].attr(trns), f=1)
    # tangent_clamp.outputB.connect(con_dict['between'][1][1].attr(trns), f=1)
    #
    # pm.delete(ptc_a, ptc_b, tangent_clamp, tangent_rev)

    con_dict['mid'][1][2].tangentConVis.connect(con_dict['between'][0][0].v)
    con_dict['mid'][1][2].tangentConVis.connect(con_dict['between'][1][0].v)
    # # pair blend for constraints
    # for ind, constGrp in enumerate([mid_sub_a_const_grp, mid_const_grp, mid_sub_b_const_grp]):
    #     const = pm.parentConstraint(con_dict['mid'][ind][2], constGrp)
    #     pb_node = create_name(side='', name=const.name(), _type='pairBlend', create=True)
    #     main_grp.disableBend.connect(pb_node.weight)
    #     const.constraintTranslate.connect(pb_node.inTranslate1)
    #     const.constraintRotate.connect(pb_node.inRotate1)
    #     pb_node.inTranslate2.set(pb_node.inTranslate1.get(), l=1)
    #     pb_node.inRotate2.set(pb_node.inRotate1.get(), l=1)
    #     for ax in 'xyz':
    #         pb_node.attr('outTranslate' + ax.upper()).connect(constGrp.attr('t' + ax), f=1)
    #         pb_node.attr('outRotate' + ax.upper()).connect(constGrp.attr('r' + ax), f=1)
    #     pm.parent(con_dict['mid'][ind][3], constGrp)
    pm.parent(con_dict['start'][1][0], con_dict['end'][1][0], con_dict['mid'][1][0], main_con_grp)

    '''Squash calculation'''
    name = create_name(side='', name=b_crv, _type='curveInfo')
    crv_info = pm.arclen(b_crv, ch=1)
    crv_info.rename(name)
    scale_fix = create_name(side='', name=full_name, fn='bendy_scaleFix', _type='multiplyDivide', create=True)
    global_scale.s.connect(scale_fix.input1)
    scale_fix.input2X.set(crv_info.arcLength.get())

    norm_node = create_name(side='', name=full_name, fn='squash_norm', _type='multiplyDivide', create=True)
    norm_node.operation.set(2)
    crv_info.arcLength.connect(norm_node.input1X)
    scale_fix.outputX.connect(norm_node.input2X)

    invr_node = create_name(side='', name=full_name, fn='squash_invr', _type='multiplyDivide', create=True)
    invr_node.operation.set(2)
    invr_node.input1X.set(1)
    norm_node.outputX.connect(invr_node.input2X)

    sqrt_node = create_name(side='', name=full_name, fn='squash_sqrt', _type='multiplyDivide', create=True)
    sqrt_node.operation.set(3)
    sqrt_node.input2X.set(.5)
    invr_node.outputX.connect(sqrt_node.input1X)

    squash_switch = create_name(side='', name=full_name, fn='squash_switch', _type='blendColors', create=True)
    main_grp.squash.connect(squash_switch.blender)
    sqrt_node.outputX.connect(squash_switch.color1R)
    squash_switch.color2R.set(1)

    vol_mult_node = create_name(side='', name=full_name, fn='squash_multiplier', _type='multiplyDivide', create=True)
    main_grp.volume.connect(vol_mult_node.input2X)
    squash_switch.outputR.connect(vol_mult_node.input1X)

    '''twist'''
    twst_main = create_name(side='', name=full_name, fn='twist_main', _type='group', create=True)
    main_util_grp.addChild(twst_main)
    pm.matchTransform(twst_main, joint_list[0])

    for ind, jnt in enumerate(joint_list):
        twist_pref = '{}_{}'.format(prefix, jnt)
        twist_parent = create_name(side='', name=twist_pref, fn='twist', _type='group', create=True)
        twst_main.addChild(twist_parent)
        twst_base = create_name(side='', name=twist_pref, fn='twistBase', _type='transform', create=True)
        twist_parent.addChild(twst_base)
        result = create_name(side='', name=twist_pref, fn='twistData', _type='transform', create=True)
        twst_base.addChild(result)
        twst_end = create_name(side='', name=twist_pref, fn='twistEnd', _type='transform', create=True)

        pm.delete(pm.parentConstraint(jnt, twist_parent))
        twist_parent.r.set([0, 0, 0])

        # make sure end jnt is pointing same direction as start jnt
        if ind + 1 < len(joint_list):
            pm.delete(pm.parentConstraint(joint_list[ind + 1], twst_end))
        else:
            tmp = pm.group(em=1, parent=jnt)
            tmp.addChild(twst_end)
            pm.delete(pm.parentConstraint(joint_list[0], tmp))
            pm.delete(pm.pointConstraint(jnt, twst_end))
            pm.delete(pm.pointConstraint(jnt, tmp))
            pm.parent(twst_end, w=1)
            pm.delete(tmp)
        pm.parent(twst_end, twist_parent)

        twst_end.r.set([0, 0, 0])

        # twist base aiming twist end
        pm.aimConstraint(twst_end, twst_base, wut='none', aimVector=aimVs[side][forward], upVector=upVs[side][forward])

        pm.pointConstraint(jnt, twst_base, mo=1)
        # to prevent flipping create a proxy with twist_base for jnt
        jnt_pxy = pm.duplicate(twst_base, name='{}_twist_pxy'.format(jnt), po=1, rr=1)[0]
        pm.parentConstraint(jnt, jnt_pxy, mo=1)

        orient_node = pm.orientConstraint(jnt_pxy, twst_base, result)

        # attribute name and multiplier
        at_name = 'Start' if ind == 0 else 'End'
        mult_val = 2 if side == 'l' else -2

        # disable blend on constraint
        orient_weight_list = orient_node.getWeightAliasList()
        main_grp.attr('twist{}Enable'.format(at_name)).connect(orient_weight_list[0])
        main_grp.attr('twist{}RotateOrder'.format(at_name)).connect(result.ro)

        # multiply rotate value by 2 to get actual rotate value
        mult = create_name(side='', name=full_name, fn='twist', _type='multiplyDivide', create=True)
        mult.i1x.set(mult_val)

        result.attr('r' + forward).connect(mult.input2X)
        if ind == 0:
            mult.outputX.connect(main_grp.twistStart)
        else:
            mult.outputX.connect(main_grp.twistEnd)

        prnt = jnt.getParent()
        if ind != 0:
            prnt = joint_list[ind - 1]
        pm.parentConstraint(prnt, twist_parent, mo=1)
        pm.scaleConstraint(prnt, twist_parent, mo=1)

    '''create nurbsSurface'''
    temp_crv_a = pm.duplicate(b_crv, rr=1)[0]
    temp_crv_b = pm.duplicate(b_crv, rr=1)[0]
    pm.xform(temp_crv_a, temp_crv_b, piv=pm.xform(main_grp, q=1, ws=1, piv=1)[:3])
    pm.parent(temp_crv_a, temp_crv_b, main_grp)
    pm.makeIdentity(temp_crv_a, temp_crv_b, a=1)

    offset_crv = [0, 0, 0.5]
    if forward == 'z':
        offset_crv = [0.5, 0, 0]

    pm.move(temp_crv_a, offset_crv[0], offset_crv[1], offset_crv[2], r=1, os=1)
    pm.move(temp_crv_b, offset_crv[0] * -1, offset_crv[1] * -1, offset_crv[2] * -1, r=1, os=1)

    name = create_name(side='', name=full_name, fn='bendy', _type='surface')
    res_surface = pm.loft(temp_crv_a, temp_crv_b, name=name,
                          ch=0, u=1, c=0, ar=1, d=1, ss=1, rn=0, po=0, rsn=True)[0]

    name = create_name(side='', name=res_surface, _type='skinCluster')
    scl_node = pm.skinCluster(surf_jnts, res_surface, name=name)

    for ind, jnt in enumerate(surf_jnts):
        pm.skinPercent(scl_node, res_surface.cv[ind][0:1], tv=[jnt, 1])

    '''create skin joints and attach them to the surface'''
    res_jnt_count = joint_count
    jnt_diff = 1.0 / (res_jnt_count - 1)
    const_diff = 1.0 / (res_jnt_count - 1)
    val = 0
    temp_loc = pm.spaceLocator()
    temp_node = pm.createNode('closestPointOnSurface')
    const = pm.parentConstraint(joint_list, temp_loc)
    weight_list = const.getWeightAliasList()
    weight_list[0].set(0)
    weight_list[1].set(1)

    temp_loc.worldPosition.connect(temp_node.inPosition)
    res_surface.worldSpace.connect(temp_node.inputSurface)

    weight_list[0].set(1 - val)
    weight_list[1].set(val)

    name = create_name(side='', name=full_name, fn='loc_main', _type='group')
    loc_main_grp = pm.group(name=name, p=main_util_grp, em=1)
    padding = len(str(res_jnt_count + 1))
    for ind in range(res_jnt_count):
        index = str(ind + 1).zfill(padding)
        pm.select(cl=1)
        jnt = create_name(side='', name=full_name, fn='bendy{}_result'.format(index), _type='joint', create=True)
        jnt_grps = common.group_pivot(jnt, layer=['offset', 'driven'])
        # jnt.inheritsTransform.set(0)
        jnt.radius.set(rad)
        joint_list[0].addChild(jnt)
        jnt.jo.set([0, 0, 0])
        jnts.append(jnt)

        loc = create_name(side='', name=full_name, fn='bendy{}_result'.format(index), _type='locator', create=True)
        jnt_grps[1].addChild(loc)

        # constrain jnt to loc
        create_matrix_constrain([loc, jnt])

        pnt_surf_info = create_name(side='', name=full_name, fn='bendy{}_result'.format(index),
                                    _type='pointOnSurfaceInfo', create=True)
        par_u = temp_node.parameterU.get()
        pnt_surf_info.parameterU.set(par_u)
        pnt_surf_info.parameterV.set(.5)
        res_surface.worldSpace.connect(pnt_surf_info.inputSurface)

        fourb4_mat = create_name(side='', name=full_name, fn='bendy{}_result'.format(index),
                                 _type='fourByFourMatrix', create=True)
        for i, ax in enumerate('xyz'):
            pnt_surf_info.attr('tangentU' + ax).connect(fourb4_mat.attr('in0{}'.format(i)))
            pnt_surf_info.attr('normal' + ax.upper()).connect(fourb4_mat.attr('in1{}'.format(i)))
            pnt_surf_info.attr('tangentV' + ax).connect(fourb4_mat.attr('in2{}'.format(i)))
            pnt_surf_info.attr('position' + ax.upper()).connect(fourb4_mat.attr('in3{}'.format(i)))

        decomp = create_name(side='', name=full_name, fn='bendy{}_result'.format(index),
                             _type='decomposeMatrix', create=True)
        fourb4_mat.output.connect(decomp.inputMatrix)
        decomp.outputTranslate.connect(jnt_grps[0].t)
        decomp.outputRotate.connect(jnt_grps[0].r)
        jnt_grps[0].inheritsTransform.set(0)
        if ind < (res_jnt_count - 1):
            val += const_diff
            weight_list[0].set(1 - val)
            weight_list[1].set(val)

        # twist system on locator
        twst_start_add_node = create_name(side='', name=full_name, fn='twist{}_start'.format(index),
                                          _type='plusMinusAverage', create=True)

        neg_node.output3Dx.connect(twst_start_add_node.input1D[0])
        con_dict['start'][1][2].twist.connect(twst_start_add_node.input1D[1])

        twst_end_add_node = create_name(side='', name=full_name, fn='twist{}_end'.format(index),
                                        _type='plusMinusAverage', create=True)
        neg_node.output3Dz.connect(twst_end_add_node.input1D[0])
        con_dict['end'][1][2].twist.connect(twst_end_add_node.input1D[1])

        twst_mult = create_name(side='', name=full_name, fn='twist{}_multiplier'.format(index),
                                _type='multiplyDivide', create=True)
        twst_start_add_node.output1D.connect(twst_mult.input1X)
        twst_end_add_node.output1D.connect(twst_mult.input1Z)
        twst_mult.input2Z.set(jnt_diff * ind)
        twst_mult.input2X.set(1 - twst_mult.input2Z.get())

        twst_amount_node = create_name(side='', name=full_name, fn='twist{}_total'.format(index),
                                       _type='plusMinusAverage', create=True)
        twst_mult.outputX.connect(twst_amount_node.input1D[0])
        twst_mult.outputZ.connect(twst_amount_node.input1D[1])
        twst_amount_node.output1D.connect(jnt_grps[1].rx)

        # squash switch
        vol_mult_node.outputX.connect(jnt_grps[1].sy)
        vol_mult_node.outputX.connect(jnt_grps[1].sz)

        pm.delete(pm.orientConstraint(joint_list[0], loc))

        # global scale
        global_scale.s.connect(jnt_grps[0].s)

        loc_main_grp.addChild(jnt_grps[0])

    '''clean up'''
    pm.delete(temp_loc, temp_node, temp_crv_a, temp_crv_b)
    pm.parent(res_surface, b_crv, main_util_grp)

    return {'result_jnts': jnts, 'main_grps': [main_nul_grp, main_util_grp], 'cons': con_dict,
            'scale_node': global_scale, 'driver': main_grp}


def create_bendy_chain(joint_list=None, side='l', name='', forward='x', up='z', con_scale=1, joint_count=5,
                       mirror=False):
    """
    create ribbon with providing exact multiple joints in joint list.
    Same as create bendy, but this will create extra mid ctrl(s).
    This will auto create a parent if first item in joint list has no parent object.
    :param name: name of system
    :param joint_count: amount of joint to be created
    :param mirror: mirror behavior of the controllers
    :param up: up axis
    :param joint_list: [list], accept two joints only
    :param side:
    :param forward: forward axis
    :param con_scale: scale of cons
    :return:
    """
    result_jnts = []
    scale_nodes = []
    const_grps = []
    main_cons = []
    name = name if name else 'temp'

    # make sure joint_list[0] has parent
    prnt_jnt = joint_list[0].getParent()
    if not prnt_jnt:
        prnt_jnt = pm.duplicate(joint_list[0], po=1,
                                name=common.replace_name(joint_list[0].name(), 'joint', 'prnt:joint'))[0]
        prnt_jnt.addChild(joint_list[0])

    # groups
    main_con_grp = common.create_name(side=side, name="{}_bendy_main".format(name), fn='con', _type='group', create=True)
    main_util_grp = common.create_name(side=side, name="{}_bendy_main".format(name), fn='util', _type='group', create=True)
    main_util_grp.visibility.set(0)

    # duplicate joint
    j_suf = common.create_name(side='', name='bendy', fn='main', _type='joint')
    j_name = common.create_name(side='', name='', _type='joint')
    new_jnts = joints.duplicate_chain(joint_list, j_name, j_suf)

    # create curve
    hard_crv, soft_crv = create_bendy_curve(joint_list=new_jnts, name=joint_list[0])
    pm.parent(hard_crv, soft_crv, main_util_grp)

    # create main bendy controllers
    for i, jnt in enumerate(new_jnts):
        name = common.replace_name(jnt.name(), 'joint', 'ctrl')
        con = shape_gen.create('cube', name=name, groups=['offset', 'driven'], color=24)
        con[-1].addAttr('twist', dv=0, k=1)
        con[-1].addAttr('tension', min=0, max=1, dv=0, k=1)
        con[-1].s.set([con_scale] * 3)
        pm.makeIdentity(con[-1], a=1, s=1)

        if mirror:
            con[1].attr('r' + forward).set(180)
            con[1].attr('s' + forward).set(-1)

        # lock attributes
        channels.cb_status(con[-1], rotates='xyz', scales='xyz', v=1, lock=1, show=0)

        # constraint con to original joint
        pm.parentConstraint(joint_list[i], con[0])

        # constraint bendy_jnt to con
        pm.parentConstraint(con[-1], jnt, mo=1)

        # clean up
        pm.parent(con[0], main_con_grp)

        main_cons.append(con[-1])

    # create bendy
    for i, jnt in enumerate(new_jnts[:-1]):
        prefix = '_'.join(joint_list[i].split('_')[1:-1])
        if prefix == '':
            prefix = create_name(side='', name=joint_list[i], _type='')

        if prefix.isdigit():
            prefix = '_'.join(joint_list[i].split('_')[:-1])

        bendy_sys = create_bendy(joint_list=[jnt, new_jnts[i + 1]], side=side, prefix=prefix, forward=forward, up=up,
                                 con_scale=con_scale, joint_count=joint_count, mirror=mirror)
        bendy_cons = bendy_sys['cons']
        scale_nodes.append(bendy_sys['scale_node'])
        result_jnts.append(bendy_sys['result_jnts'])
        grps = []
        for key in ['start', 'mid', 'end', 'between']:
            for item in bendy_cons[key]:
                if not item:
                    continue
                grps.append(item[0])
                if pm.pointConstraint(item[0], q=1):
                    pm.delete(pm.pointConstraint(item[0], q=1))

                # connect twist attr and hide it
                if key == 'start':
                    main_cons[i].twist.connect(item[2].twist)
                    item[2].twist.set(l=1, k=0, cb=0)
                elif key == 'end':
                    main_cons[i + 1].twist.connect(item[2].twist)
                    item[2].twist.set(l=1, k=0, cb=0)

        # parent group
        pm.parent(bendy_sys['main_grps'][0], main_con_grp)
        pm.parent(bendy_sys['main_grps'][-1], main_util_grp)

        # reorder and sort grps for per section
        new_grps = [grps[0], grps[3], grps[1], grps[4], grps[2]]
        if not const_grps:
            # for first group
            const_grps.append(new_grps[:3])
        else:
            const_grps[-1].extend(new_grps[:3])

        const_grps.append((new_grps[-2:]))

    # create nodes to blend joints' position between hard and soft bend curves
    for q, grp in enumerate(const_grps):
        for i, g in enumerate(grp):
            poci_soft = common.create_closest_poci([g, soft_crv], prefix='softCrv', locator=False)[0]
            poci_hard = common.create_closest_poci([g, hard_crv], prefix='hardCrv', locator=False)[0]

            blend = create_name(side='', name=g, _type='blendColors', create=True)
            blend.blender.set(0)
            poci_soft.position.connect(blend.color1)
            poci_hard.position.connect(blend.color2)

            fbf = create_name(side='', name=g, fn='const', _type='fourByFourMatrix', create=True)
            blend.outputR.connect(fbf.in30)
            blend.outputG.connect(fbf.in31)
            blend.outputB.connect(fbf.in32)

            mult_mat = create_name(side='', name=g, fn='const', _type='multMatrix', create=True)
            fbf.output.connect(mult_mat.matrixIn[0])

            if 'midA' not in g.name() and 'midB' not in g.name():
                g.parentInverseMatrix.connect(mult_mat.matrixIn[1])
            else:
                g.getParent().parentInverseMatrix.connect(mult_mat.matrixIn[1])

            dcmp_mat = create_name(side='', name=g, fn='const', _type='decomposeMatrix', create=True)
            mult_mat.matrixSum.connect(dcmp_mat.inputMatrix)
            dcmp_mat.outputTranslate.connect(g.t)

            # connect tension attr
            main_cons[q].tension.connect(blend.blender)

    # controllers scale constraint
    pm.parentConstraint(new_jnts[0].getParent(), main_con_grp)
    pm.scaleConstraint(new_jnts[0].getParent(), main_con_grp)

    # hide new_jnts for cleaner viewport
    [j.drawStyle.set(2) for j in new_jnts]

    return [main_con_grp, new_jnts, result_jnts, main_util_grp]


def create_bendy_curve(joint_list=None, name=''):
    """
    create two curves with provided joints
    :param joint_list: [list of joint]
    :param name: name of curve
    :return: [hard curve and soft curve]
    """
    if joint_list is None:
        return
    if name == '':
        name = joint_list[0].name()
    hard_pos_list = []
    hard_crv_skin = []
    soft_pos_list = []
    soft_crv_skin = []

    for i, jnt in enumerate(joint_list):
        pos = [round(q, 3) for q in jnt.getTranslation(space='world')]

        # append twice for hard bend curve
        hard_pos_list.append(pos)
        hard_pos_list.append(pos)
        skin = [0 for q in range(len(joint_list))]
        skin[i] = 1
        hard_crv_skin.extend(skin)
        hard_crv_skin.extend(skin)

        # soft bend curve
        if i == 0 or i + 1 == len(joint_list):
            # first and last joint
            soft_pos_list.append(pos)
            soft_pos_list.append(pos)
            soft_crv_skin.extend(skin)
            soft_crv_skin.extend(skin)

        else:
            soft_pos_list.append(pos)
            soft_crv_skin.extend(skin)

    hard_crv = pm.curve(p=hard_pos_list, d=2, name='{}_bendy_hard_crv'.format(name))
    soft_crv = pm.curve(p=soft_pos_list, d=2, name='{}_bendy_soft_crv'.format(name))

    # skinning
    hard_scl = skinning.create_scl(hard_crv, joint_list)
    hard_scl.setWeights(hard_crv.getShapes(ni=1)[0], range(len(joint_list)), hard_crv_skin, False)
    soft_scl = skinning.create_scl(soft_crv, joint_list)
    soft_scl.setWeights(soft_crv.getShapes(ni=1)[0], range(len(joint_list)), soft_crv_skin, False)

    return [hard_crv, soft_crv]
