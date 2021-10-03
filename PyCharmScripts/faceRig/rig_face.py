import pymel.all as pm

import PyCharmScripts.utils.ribbon
import PyCharmScripts.utils.rivet
from ..data import name_data
from ..utils import common, vertsFunc as vf, skinning
from PyCharmScripts.tools.controllerShape import colors, main as shape_gen

reload(vf)
reload(common)
reload(skinning)
reload(shape_gen)
reload(colors)


def set_clus_weight(clus, weight_dict):
    """
    set cluster weight
    :param clus:
    :param weight_dict:
    :return:
    """
    if not isinstance(clus, pm.Cluster):
        print 'First argument must be a cluster node.'
        return

    geoms = clus.getGeometry()
    for i, geom in enumerate(geoms):
        if geom in weight_dict.keys():
            for u, x in enumerate(weight_dict[geom]):
                if isinstance(geom, pm.Mesh):
                    clus.setWeight(geom, i, pm.PyNode(geom).vtx[u], w)
                    continue
                for v, w in enumerate(x):
                    '''
                        setWeight(self, path, index, components, weight, oldValues=None)
                     |      Sets the weights of the specified components of the object whose DAG path is specified.
                     |      
                     |      :Parameters:
                     |          path : `PyNode`
                     |              the DAG path for the object whose components' weights are being set 
                     |          index : `int`
                     |              the plug index for the specified shape 
                     |          components : `PyNode`
                     |              the components of the object 
                     |          weight : `float`
                     |              weight value for the components 
                     |          oldValues : `float` list
                     |              an array of old values for the components
                        '''
                    clus.setWeight(geom, i, pm.PyNode(geom).cv[u][v], w)


def create_zip_system(up_lip_zip, lo_lip_zip, up_lip_skin, lo_lip_skin):
    """
    create zip system by providing surfaces
    :param up_lip_zip:
    :param lo_lip_zip:
    :param up_lip_skin:
    :param lo_lip_skin:
    :return: up_lip_result, lo_lip_result, ctrl
    """
    # duplicate lip surface
    up_lip_result = pm.duplicate(up_lip_skin, rr=1, name=up_lip_skin.replace('skin', 'result'))[0]
    lo_lip_result = pm.duplicate(lo_lip_skin, rr=1, name=lo_lip_skin.replace('skin', 'result'))[0]

    # copy skin weight
    skinning.copy_skin([up_lip_skin, up_lip_zip], one_to_one=True)
    skinning.copy_skin([lo_lip_skin, lo_lip_zip], one_to_one=True)

    # modify weight
    for lip in [up_lip_zip, lo_lip_zip]:
        scl = skinning.get_skin_cluster(lip)
        shape = scl.getGeometry()[0]
        jnts = scl.getInfluence()
        weights = [q for q in scl.getWeights(lip)]
        weight_length = len(weights)
        start = weights[0]
        weight_array = []
        for i in range(weight_length):
            weight_array.extend(start)

        scl.setWeights(shape, range(len(jnts)), weight_array, False)

    # create blendshape node
    bld_suffix = name_data.TYPE_LIST['blendShape']
    up_bld = pm.blendShape(up_lip_skin, up_lip_zip, up_lip_result, name="{}_{}".format(up_lip_result, bld_suffix))[0]
    lo_bld = pm.blendShape(lo_lip_skin, lo_lip_zip, lo_lip_result, name="{}_{}".format(lo_lip_result, bld_suffix))[0]

    # set blendshape weight
    for i in range(2):
        up_bld.setWeight(i, 1)
        lo_bld.setWeight(i, 1)

    ctrl = common.create_name(side='', name='lips_zip', fn='ctrl', _type='group', create=True)

    ctrl.addAttr('zip_a', at='double', min=0, max=1, k=1, dv=0)
    ctrl.addAttr('zip_b', at='double', min=0, max=1, k=1, dv=0)

    u_count = up_lip_zip.numCVsInU()
    v_count = up_lip_zip.numCVsInV()

    padding = len(str(v_count + 1))

    increment = 2
    diff = 1.0 / (increment + v_count - 1)
    position_a = 0
    position_b = diff * increment

    position_x = 1 - position_b
    position_y = 1

    for v in range(v_count):
        remap_a = common.create_name(side='', name='lips', fn='zipA', _type='remapValue', create=True)
        remap_a.value[0].value_Position.set(position_a)
        remap_a.value[0].value_FloatValue.set(0)
        remap_a.value[1].value_Position.set(position_b)
        remap_a.value[1].value_FloatValue.set(1)

        position_a += diff
        position_b += diff

        remap_b = common.create_name(side='', name='lips', fn='zipB', _type='remapValue', create=True)
        remap_b.value[0].value_Position.set(position_x)
        remap_b.value[0].value_FloatValue.set(0)
        remap_b.value[1].value_Position.set(position_y)
        remap_b.value[1].value_FloatValue.set(1)

        position_x -= diff
        position_y -= diff
        ctrl.zip_a.connect(remap_a.inputValue)
        ctrl.zip_b.connect(remap_b.inputValue)
        # if first_on == 'r':
        #     ctrl.l_zip.connect(remap_a.inputValue)
        #     ctrl.r_zip.connect(remap_b.inputValue)
        # else:
        #     ctrl.r_zip.connect(remap_a.inputValue)
        #     ctrl.l_zip.connect(remap_b.inputValue)

        sum_lip = common.create_name(side='', name='lips', fn='zip_sum', _type='plusMinusAverage', create=True)
        remap_a.outValue.connect(sum_lip.input1D[0])
        remap_b.outValue.connect(sum_lip.input1D[1])

        clamp = common.create_name(side='', name='lips', fn='zip', _type='clamp', create=True)
        sum_lip.output1D.connect(clamp.inputR)
        clamp.maxR.set(1)

        rev = common.create_name(side='', name='lips', fn='zip', _type='reverse', create=True)
        clamp.outputR.connect(rev.inputX)

        for u in range(u_count):
            ind = (u * v_count) + v
            for bld in [up_bld, lo_bld]:
                rev.inputX.connect(bld.inputTarget[0].inputTargetGroup[1].targetWeights[ind])
                rev.outputX.connect(bld.inputTarget[0].inputTargetGroup[0].targetWeights[ind])
        # clamp.outputR.connect
    return up_lip_result, lo_lip_result, ctrl, [up_bld, lo_bld]


def create_lips_rig(edgs, side=None, up=None, down=None, con_count=5, con_scale=1, attach_to=None):
    """
    create lips rig with multiple inputs
    :param edgs: whole mouth edge loop
    :param side: vertices on two sides of the mouth
    :param up: up lip middle
    :param down: lo lip middle
    :param con_count: number of controller
    :param con_scale: scale of controller
    :param attach_to: constrain objects generated by this script to an object
    :return:
    """
    main_con_scale = con_scale * 1.5
    con_main_grp = common.create_name(side='', name='lips_{}'.format(name_data.TYPE_LIST['ctrl']), fn='main',
                                      _type='group', create=True)
    jnt_main_grp = common.create_name(side='', name='lips_{}'.format(name_data.TYPE_LIST['joint']), fn='main',
                                      _type='group', create=True)
    jnt_main_grp.v.set(0)

    # no touch group
    no_touch = pm.group(name='lips_noTouch', em=1)
    common.parent_to_no_touch(no_touch)
    no_touch.v.set(0)

    head_mesh = edgs[0].node()

    for edg in edgs:
        if not isinstance(edg, pm.MeshEdge):
            print "---Inputs contain non mesh edge element.---"
            return
    vtxs = pm.polyListComponentConversion(edgs, fe=1, tv=1)
    vtxs = pm.ls(vtxs, fl=1)
    if side:
        if len(side) == 1:
            tmp = vf.find_symmetric(side[0])
            side = [side[0], tmp[side[0]]]
        side_dict = vf.find_side_vtx(side)
        # after finding left and right, define 'zero'
        tmp = vf.find_side_vtx(vtxs)
        side_dict['zero'] = tmp['zero']
    else:
        side_dict = vf.find_side_vtx(vtxs)

    # reorder 'zero' based on its y-axis value
    side_dict['zero'] = sorted(side_dict['zero'], key=lambda vid: abs(round(vid.getPosition(space='world')[1], 3)))

    if not up:
        up = side_dict['zero'][-1]
    if not down:
        down = side_dict['zero'][0]

    # find and sort vertices for upLip and loLip
    tmp_vtxs = pm.polySelectSp(side_dict['far'], loop=True)
    tmp_vtxs = [v for v in pm.ls(tmp_vtxs, fl=1) if v in vtxs]
    if up in tmp_vtxs:
        up_vtxs = tmp_vtxs
        lo_vtxs = [v for v in vtxs if v not in up_vtxs]
        lo_vtxs.extend(side_dict['far'])
    else:
        lo_vtxs = tmp_vtxs
        up_vtxs = [v for v in vtxs if v not in lo_vtxs]
        up_vtxs.extend(side_dict['far'])

    up_edg = pm.polyListComponentConversion(up_vtxs, fv=1, te=1, internal=1)
    lo_edg = pm.polyListComponentConversion(lo_vtxs, fv=1, te=1, internal=1)

    pm.select(up_edg)
    up_crv = pm.PyNode(pm.polyToCurve(form=2, degree=1, ch=0, name='up_lip_crv')[0])
    pm.select(lo_edg)
    lo_crv = pm.PyNode(pm.polyToCurve(form=2, degree=1, ch=0, name='lo_lip_crv')[0])

    # check end of curve are on same position
    if up_crv.cv[0].getPosition(space='world') != lo_crv.cv[0].getPosition(space='world'):
        pm.reverseCurve(rpo=1, ch=0)

    # rebuild for cubic degree
    pm.rebuildCurve(up_crv, ch=0, d=3, rpo=1, kcp=1, kr=2, rt=0)
    pm.rebuildCurve(lo_crv, ch=0, d=3, rpo=1, kcp=1, kr=2, rt=0)

    tmp_up = pm.duplicate(up_crv, rr=1, name='{}_tmp'.format(up_crv))[0]
    tmp_lo = pm.duplicate(lo_crv, rr=1, name='{}_tmp'.format(lo_crv))[0]

    # use loft to create nurbsSurface
    up_crv.tz.set(.01)
    tmp_up.tz.set(-.01)

    lo_crv.tz.set(.01)
    tmp_lo.tz.set(-.01)

    loft_argvs = {'ch': 0, 'd': 3, 'u': 1, 'c': 0, 'ar': 1}
    surf_name = common.create_name(create=False, side='', _type='surface', fn='dvr_skin', name='{}_lip')
    up_skin_surf = pm.loft([up_crv, tmp_up], name=surf_name.format('up'), **loft_argvs)[0]
    lo_skin_surf = pm.loft([lo_crv, tmp_lo], name=surf_name.format('lo'), **loft_argvs)[0]

    # rebuild surface to match con count
    rebuild_argvs = {"rt": 0, "ch": 0, "rpo": 1, "du": 1, "su": 1, "dv": 3, "sv": (con_count - 1) * 2}
    pm.rebuildSurface(up_skin_surf, **rebuild_argvs)
    pm.rebuildSurface(lo_skin_surf, **rebuild_argvs)

    # surfaces for other system
    up_zip_surf = pm.duplicate(up_skin_surf, rr=1, name=up_skin_surf.replace('skin', 'zip'))[0]
    lo_zip_surf = pm.duplicate(lo_skin_surf, rr=1, name=lo_skin_surf.replace('skin', 'zip'))[0]

    up_twk_surf = pm.duplicate(up_skin_surf, rr=1, name=up_skin_surf.replace('skin', 'tweak'))[0]
    lo_twk_surf = pm.duplicate(lo_skin_surf, rr=1, name=lo_skin_surf.replace('skin', 'tweak'))[0]

    '''lip clusters'''
    # upLip, loLip and mouth corner controllers and function
    corner_mid_dist = up.getPosition(space='world').distanceTo(up_vtxs[-1].getPosition(space='world'))

    up_soft_select_argvs = {'scc': '1,1,0,1,1,1,0,0,0.5,1,0,0,0,0,1',
                            'ssc': '1,0.5,2,0,1,2,1,0,2',
                            'ssd': corner_mid_dist,
                            'sse': 1,
                            'ssf': 1}

    side_soft_select_argvs = {'scc': '1,1,0,1,1,1,0,0,0.5,1,0,0,0,0,1',
                              'ssc': '0,1,0,1,0,1,0,1,1',
                              'ssd': corner_mid_dist,
                              'sse': 1,
                              'ssf': 1}

    ori_soft_select_argvs = {'scc': pm.softSelect(q=1, scc=1),
                             'ssc': pm.softSelect(q=1, ssc=1),
                             'ssd': pm.softSelect(q=1, ssd=1),
                             'sse': pm.softSelect(q=1, sse=1),
                             'ssf': pm.softSelect(q=1, ssf=1)}

    pm.softSelect(**up_soft_select_argvs)

    pm.select(up_skin_surf.cv[0:1][con_count], up_zip_surf.cv[0:1][con_count], up_twk_surf.cv[0:1][con_count])
    up_soft = common.get_soft_selection_weight()

    pm.select(lo_skin_surf.cv[0:1][con_count], lo_zip_surf.cv[0:1][con_count], lo_twk_surf.cv[0:1][con_count])
    lo_soft = common.get_soft_selection_weight()

    pm.softSelect(**side_soft_select_argvs)

    pm.select(up_skin_surf.cv[0:1][0], lo_skin_surf.cv[0:1][0],
              up_zip_surf.cv[0:1][0], lo_zip_surf.cv[0:1][0],
              up_twk_surf.cv[0:1][0], lo_twk_surf.cv[0:1][0])
    zero_soft = common.get_soft_selection_weight()

    pm.select(up_skin_surf.cv[0:1][-1], lo_skin_surf.cv[0:1][-1],
              up_zip_surf.cv[0:1][-1], lo_zip_surf.cv[0:1][-1],
              up_twk_surf.cv[0:1][-1], lo_twk_surf.cv[0:1][-1])
    last_soft = common.get_soft_selection_weight()

    # find zero and final cv location for side prefix
    if pm.xform(up_skin_surf.cv[0][0], q=1, ws=1, t=1)[0] > 0:
        zero_prefix = 'left'
        last_prefix = 'right'
    else:
        zero_prefix = 'right'
        last_prefix = 'left'

    # create cluster and set weight
    # all
    all_clus = common.create_name(create=False, side='', name='all_lip', _type='cluster')
    all_clus, all_clus_handle = pm.cluster(up_skin_surf, lo_skin_surf,
                                           up_zip_surf, lo_zip_surf,
                                           name=all_clus, relative=True)
    pm.xform(all_clus_handle, ws=1, piv=pm.xform(up_skin_surf.cv[0][con_count], q=1, ws=1, t=1))

    pm.softSelect(**ori_soft_select_argvs)

    # up_lip
    up_clus = common.create_name(create=False, side='', name='up_lip', _type='cluster')
    up_clus, up_clus_handle = pm.cluster(up_skin_surf, up_zip_surf, name=up_clus, relative=True)
    pm.xform(up_clus_handle, ws=1, piv=pm.xform(up_skin_surf.cv[0][con_count], q=1, ws=1, t=1))
    set_clus_weight(up_clus, up_soft)

    # lo_lip
    lo_clus = common.create_name(create=False, side='', name='lo_lip', _type='cluster')
    lo_clus, lo_clus_handle = pm.cluster(lo_skin_surf, lo_zip_surf, name=lo_clus, relative=True)
    pm.xform(lo_clus_handle, ws=1, piv=pm.xform(lo_skin_surf.cv[0][con_count], q=1, ws=1, t=1))
    set_clus_weight(lo_clus, lo_soft)

    # corners
    zero_clus = common.create_name(create=False, side=zero_prefix, name='mouthCorner', _type='cluster')
    zero_clus, zero_clus_handle = pm.cluster(up_skin_surf, lo_skin_surf,
                                             up_zip_surf, lo_zip_surf,
                                             name=zero_clus, relative=True)
    pm.xform(zero_clus_handle, ws=1, piv=pm.xform(up_skin_surf.cv[0][0], q=1, ws=1, t=1))
    set_clus_weight(zero_clus, zero_soft)

    last_clus = common.create_name(create=False, side=last_prefix, name='mouthCorner', _type='cluster')
    last_clus, last_clus_handle = pm.cluster(up_skin_surf, lo_skin_surf,
                                             up_zip_surf, lo_zip_surf,
                                             name=last_clus, relative=True)
    pm.xform(last_clus_handle, ws=1, piv=pm.xform(up_skin_surf.cv[0][-1], q=1, ws=1, t=1))
    set_clus_weight(last_clus, last_soft)

    # group cluster and parent under no touch
    clus_grp = common.create_name(side='', name='lips', fn='clus', _type='group', create=True)
    pm.parent(all_clus_handle, up_clus_handle, lo_clus_handle, zero_clus_handle, last_clus_handle, clus_grp)

    '''lip cluster controllers'''
    up_dict = PyCharmScripts.utils.rivet.create_obj_attach_mesh(up, prefix='up_lip_main', joint=False, nullify=attach_to)
    up_lip_con = up_dict['cons'][0]
    lo_dict = PyCharmScripts.utils.rivet.create_obj_attach_mesh(down, prefix='lo_lip_main', joint=False, nullify=attach_to)
    lo_lip_con = lo_dict['cons'][0]
    corner_dict = PyCharmScripts.utils.rivet.create_obj_attach_mesh([side_dict['far'][0]], prefix='mouthCorner', joint=False,
                                                                    nullify=attach_to)

    if name_data.SIDE_LIST[zero_prefix] in corner_dict['cons'][0].split("_")[0]:
        zero_con = corner_dict['cons'][0]
        last_con = corner_dict['cons'][1]
    else:
        zero_con = corner_dict['cons'][1]
        last_con = corner_dict['cons'][0]

    # create custom shape and replace mouth corner controllers
    temp = shape_gen.create('triangle', groups=[])
    pm.xform(temp, ws=1, piv=[0, 0, 1], r=1)
    shape_gen.swap_curve(temp, [up_lip_con, lo_lip_con, zero_con, last_con], keep_source=False)

    up_lip_con.r.set([90, 0, 0])
    lo_lip_con.r.set([-90, 0, 0])
    zero_con.r.set([90, 0, -90])
    last_con.r.set([90, 0, -90])
    for con in [up_lip_con, lo_lip_con, zero_con, last_con]:
        con.s.set([main_con_scale] * 3)

    pm.makeIdentity(up_lip_con, lo_lip_con, zero_con, last_con, a=1, t=1, r=1, s=1)

    # set controllers color
    # colors.override_shape([up_lip_con, lo_lip_con], side='middle')
    # colors.override_shape(zero_con, side=zero_prefix)
    # colors.override_shape(last_con, side=last_prefix)

    # all lip controller
    all_lip_name = common.create_name(side='middle', name='all_lip', _type='ctrl')
    all_lip = shape_gen.create('square', name=all_lip_name, groups=['nul'], color='middle')
    all_lip[-1].r.set([90, 0, 45])
    all_lip[-1].s.set([main_con_scale] * 3)
    pm.makeIdentity(all_lip[-1], a=1, r=1, s=1)
    pm.matchTransform(all_lip[0], all_clus_handle)

    # # offset con shape
    # pm.move(0, 0, .1, up_lip_con.cv, lo_lip_con.cv, zero_con.cv, last_con.cv, all_lip[-1].cv, r=1, ws=1)

    # connect cons to cluster
    for at in 'trs':
        all_lip[-1].attr(at).connect(all_clus_handle.attr(at))
        up_lip_con.attr(at).connect(up_clus_handle.attr(at))
        lo_lip_con.attr(at).connect(lo_clus_handle.attr(at))
        zero_con.attr(at).connect(zero_clus_handle.attr(at))
        last_con.attr(at).connect(last_clus_handle.attr(at))

    # disable inherit transform on control
    for d in [corner_dict, up_dict, lo_dict]:
        for pos in d['pos_grps']:
            pos.inheritsTransform.set(0)

    # add pivot controller on up and lo lip controllers
    up_piv = shape_gen.add_pivot_ctrl(up_lip_con, con_scale=con_scale)
    lo_piv = shape_gen.add_pivot_ctrl(lo_lip_con, con_scale=con_scale)
    #
    for piv, hand in {up_piv: up_clus_handle, lo_piv: lo_clus_handle}.iteritems():
        plus_piv = common.create_name(side='', name=piv, _type='plusMinusAverage', create=True)
        plus_piv.input3D[0].set(hand.rotatePivot.get())
        piv.t.connect(plus_piv.input3D[1])
        plus_piv.output3D.connect(hand.rotatePivot)
        plus_piv.output3D.connect(hand.scalePivot)

    # mirror behavior
    mirror_side = last_prefix if zero_prefix == 'left' else zero_prefix
    mirror_handle = last_clus_handle if zero_prefix == 'left' else zero_clus_handle

    trans_mir = common.create_name(side=mirror_side, name='mouthCorner', fn='trans_mirror', _type='multiplyDivide',
                                   create=True)
    trans_mir.input2.set([-1, 1, 1])
    mirror_handle.t.insertInput(trans_mir, 'output', 'input1')

    rot_mir = common.create_name(side=mirror_side, name='mouthCorner', fn='rot_mirror', _type='multiplyDivide',
                                 create=True)
    rot_mir.input2.set([1, -1, -1])
    mirror_handle.r.insertInput(rot_mir, 'output', 'input1')

    '''skinning'''
    # remove curve transform value
    tmp_up.tz.set(0)
    tmp_lo.tz.set(0)

    # rebuild to match con count
    pm.rebuildCurve(tmp_up, ch=0, d=3, rpo=1, s=(con_count - 1) * 2)
    pm.rebuildCurve(tmp_lo, ch=0, d=3, rpo=1, s=(con_count - 1) * 2)

    if skinning.get_skin_cluster(head_mesh):
        # extract faces around vtxs to make curves and surfaces have cleaner skinning
        ext_up_vtxs = sorted(up_vtxs, key=lambda vt: round(vt.getPosition(space='world')[0], 4))[1:-1]
        up_mesh = common.extract_faces(ext_up_vtxs)
        ext_lo_vtxs = sorted(lo_vtxs, key=lambda vt: round(vt.getPosition(space='world')[0], 4))[1:-1]
        lo_mesh = common.extract_faces(ext_lo_vtxs)

        skinning.copy_skin([head_mesh, up_mesh, lo_mesh])
        skinning.copy_skin([up_mesh, tmp_up])
        skinning.copy_skin([lo_mesh, tmp_lo])

        skinning.copy_crv_weight(tmp_up, up_skin_surf)
        skinning.copy_crv_weight(tmp_lo, lo_skin_surf)

    '''zip system'''
    up_result_surf, lo_result_surf, zip_con, bshps = create_zip_system(up_zip_surf, lo_zip_surf,
                                                                       up_skin_surf, lo_skin_surf)

    zero_con.addAttr('zip', at='double', min=0, max=1, dv=0, k=1)
    zero_con.zip.connect(zip_con.zip_a)

    last_con.addAttr('zip', at='double', min=0, max=1, dv=0, k=1)
    last_con.zip.connect(zip_con.zip_b)

    # add tweak surface to blendshape
    bshps[0].addTarget(up_result_surf.getShapes(ni=1)[0], 2, up_twk_surf.getShapes(ni=1)[0], 1)
    bshps[0].setWeight(2, 1)
    bshps[1].addTarget(lo_result_surf.getShapes(ni=1)[0], 2, lo_twk_surf.getShapes(ni=1)[0], 1)
    bshps[1].setWeight(2, 1)

    '''create micro controllers'''
    # proxies
    up_cons = PyCharmScripts.utils.ribbon.create_obj_on_surface(up_result_surf, num=con_count, shp_scale=con_scale, new_name='up_lip_dvr',
                                                                auto_prefix=True, rot=False)
    lo_cons = PyCharmScripts.utils.ribbon.create_obj_on_surface(lo_result_surf, num=con_count, shp_scale=con_scale, new_name='lo_lip_dvr',
                                                                auto_prefix=True, rot=False)

    up_twk_cons = []
    lo_twk_cons = []
    up_twk_jnts = []
    lo_twk_jnts = []

    # proxy to store placement for corner tweaker
    corner_tweak_locs = [pm.spaceLocator(), pm.spaceLocator()]
    pm.matchTransform(corner_tweak_locs[0], up_cons['locs'][0])
    pm.matchTransform(corner_tweak_locs[1], up_cons['locs'][-1])

    # shift first and last joint for corner tweaker
    for locs in [up_cons['locs'], lo_cons['locs']]:
        at = 'paramU'
        if locs[0].getParent(generations=2).attr(at).get() != 0:
            at = 'paramV'
        val = locs[1].getParent(generations=2).attr(at).get() / 4.0
        locs[0].getParent(generations=2).attr(at).set(val)

        last_val = locs[-1].getParent(generations=2).attr(at).get()
        val = (last_val - (last_val - locs[-2].getParent(generations=2).attr(at).get()) / 4.0)
        locs[-1].getParent(generations=2).attr(at).set(val)

    # rename and create joint
    for cons in [up_cons['main_grp'], lo_cons['main_grp']]:
        for child in cons.getChildren(ad=1, s=0):
            # create joint
            if hasattr(child, 'getShapes'):
                if child.getShapes():
                    twk_name = child.name().replace('dvr', 'tweak').replace('_loc', '')
                    if '_up_' in child.name():
                        pxy_vt = vf.find_closest_point([child, up_mesh])
                    else:
                        pxy_vt = vf.find_closest_point([child, lo_mesh])
                    vt = vf.find_closest_point([pxy_vt, head_mesh.getParent()])
                    cons = PyCharmScripts.utils.rivet.create_obj_attach_mesh([vt], joint=True, prefix=twk_name, find_symmetry=False,
                                                                             nullify=attach_to)

                    if '_up_' in child.name():
                        up_twk_cons.extend(cons['cons'])
                        up_twk_jnts.extend(cons['jnts'])
                    else:
                        lo_twk_cons.extend(cons['cons'])
                        lo_twk_jnts.extend(cons['jnts'])

    # change controllers shape
    tmp_con = shape_gen.create('dome', name='temp', groups=[])
    # tmp_con.rz.set(90)
    tmp_con.s.set([con_scale] * 3)
    pm.makeIdentity(tmp_con, a=1, s=1, r=1)
    shape_gen.swap_curve(tmp_con, up_twk_cons)

    tmp_con.rz.set(-180)
    pm.makeIdentity(tmp_con, a=1, s=1, r=1)
    shape_gen.swap_curve(tmp_con, lo_twk_cons)

    # corner tweaker
    corner_twk_jnts = []
    con_name = '{}tweak'.format(up_cons['locs'][0].replace('up_lip', 'lip_corner').split('dvr')[0])
    a_twk_dict = PyCharmScripts.utils.rivet.create_obj_attach_mesh([vf.find_closest_point([corner_tweak_locs[0], head_mesh.getParent()])],
                                                                   prefix=con_name, joint=True, con_shape='sphere',
                                                                   nullify=attach_to, find_symmetry=False, con_scale=con_scale)
    corner_twk_jnts.extend(a_twk_dict['jnts'])

    con_name = '{}tweak'.format(up_cons['locs'][-1].replace('up_lip', 'lip_corner').split('dvr')[0])
    b_twk_dict = PyCharmScripts.utils.rivet.create_obj_attach_mesh([vf.find_closest_point([corner_tweak_locs[-1], head_mesh.getParent()])],
                                                                   prefix=con_name, joint=True, con_shape='sphere',
                                                                   nullify=attach_to, find_symmetry=False, con_scale=con_scale)
    corner_twk_jnts.extend(b_twk_dict['jnts'])

    pm.delete(tmp_con, up_cons['main_grp'], lo_cons['main_grp'], up_mesh, lo_mesh, corner_tweak_locs)

    '''skin joints'''
    up_dvn_scl = skinning.create_scl(up_twk_surf, up_twk_jnts, corner_twk_jnts, dr=2)
    lo_dvn_scl = skinning.create_scl(lo_twk_surf, lo_twk_jnts, corner_twk_jnts, dr=2)

    # make weight uniform between u or v
    for scl in [up_dvn_scl, lo_dvn_scl]:
        jnts = scl.getInfluence()
        shp = scl.getGeometry()[0]
        weights = [w for w in scl.getWeights(shp)]
        weights = weights[len(weights) / 2:] * 2
        weight_array = []
        for w in weights:
            weight_array.extend(w)
        scl.setWeights(shp, range(len(jnts)), weight_array, False)

    '''skin joints'''
    up_objs = PyCharmScripts.utils.ribbon.create_obj_on_surface(up_result_surf, shp_scale=con_scale,
                                                                source=[v.getPosition(space='world') for v in up_vtxs], new_name='up_lip',
                                                                auto_prefix=True)
    lo_objs = PyCharmScripts.utils.ribbon.create_obj_on_surface(lo_result_surf, shp_scale=con_scale,
                                                                source=[v.getPosition(space='world') for v in lo_vtxs], new_name='lo_lip',
                                                                auto_prefix=True)

    # pm.parent(up_objs['main_grp'], lo_objs['main_grp'], jnt_main_grp)

    # create skin joint and replace object in group
    for cons in [up_objs['main_grp'], lo_objs['main_grp']]:
        # cons.rename(cons.replace('loc', 'jnt'))
        for obj in cons.getChildren(ad=1):
            # obj.rename(obj.replace('loc', 'jnt'))
            if hasattr(obj, 'getShapes'):
                if obj.getShapes():
                    pm.select(cl=1)
                    jnt = pm.joint(name=obj.replace('loc', 'jnt'))
                    pm.parentConstraint(obj, jnt, mo=0)
                    # obj.rename(obj + '_tmp')
                    # pm.matchTransform(jnt, obj)
                    # obj.getParent().addChild(jnt)
                    # pm.delete(obj)
                    jnt_main_grp.addChild(jnt)

    # locator to keep con_shape scale following the rig
    con_scale_loc = common.create_name(side='', name='lip', fn='scale', _type='locator')
    con_scale_loc = pm.spaceLocator(name=con_scale_loc)
    no_touch.addChild(con_scale_loc)

    if attach_to:
        pm.parentConstraint(attach_to, clus_grp, mo=1)
        pm.scaleConstraint(attach_to, clus_grp, mo=1)

        pm.parentConstraint(attach_to, con_main_grp, mo=1)
        pm.scaleConstraint(attach_to, con_main_grp, mo=1)
        # up_cons['main_grp'].inheritsTransform.set(0)
        # lo_cons['main_grp'].inheritsTransform.set(0)

        pm.scaleConstraint(attach_to, con_scale_loc, mo=1)

    # clean up
    pm.parent(up_result_surf, lo_result_surf, up_skin_surf, lo_skin_surf,
              up_zip_surf, lo_zip_surf, up_twk_surf, lo_twk_surf,
              clus_grp, zip_con, up_objs['main_grp'], lo_objs['main_grp'], no_touch)
    pm.parent(corner_dict['pos_grps'],
              up_dict['pos_grps'], lo_dict['pos_grps'], all_lip[0], 'attachMesh_con_grp', con_main_grp)

    pm.delete(up_crv, lo_crv, tmp_lo, tmp_up)

    pm.select(cl=1)
