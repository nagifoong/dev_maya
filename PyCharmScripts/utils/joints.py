import maya.OpenMaya as om
import pymel.all as pm

import channels
import common
import skinning
import attributes
from ..tools.controllerShape import main as shape_gen
from .common import create_name, atName
from ..data import name_data

reload(common)
reload(skinning)
reload(channels)
reload(attributes)
reload(name_data)
reload(shape_gen)


def find_pv(jnt_list, multiplier=5):
    start = pm.xform(jnt_list[0], q=1, ws=1, t=1)
    mid = pm.xform(jnt_list[1], q=1, ws=1, t=1)
    end = pm.xform(jnt_list[2], q=1, ws=1, t=1)

    start_v = om.MVector(start[0], start[1], start[2])
    mid_v = om.MVector(mid[0], mid[1], mid[2])
    end_v = om.MVector(end[0], end[1], end[2])
    start_end = end_v - start_v
    start_mid = mid_v - start_v
    dot_p = start_mid * start_end
    proj = float(dot_p) / float(start_end.length())
    start_end_n = start_end.normal()
    proj_v = start_end_n * proj
    arrow_v = start_mid - proj_v
    # arrow_v += [start_mid.length()/3 for q in range(3)]
    final_v = (arrow_v * multiplier) + mid_v
    # print start_mid.length()
    return [final_v.x, final_v.y, final_v.z]


def set_joint_vis(v=True, status=False):
    """
    Show/ hide joints
    :param status: print operation type
    :param v:
    :return:
    """
    for jnt in pm.ls(type='joint'):
        if jnt.drawStyle.isConnected() or jnt.drawStyle.isLocked():
            continue
        if v:
            jnt.drawStyle.set(2)
            if status:
                pm.warning("==JOINT== Hiding Joints.")
        else:
            jnt.drawStyle.set(0)
            if status:
                pm.warning("==JOINT== Showing Joints.")


def set_joint_label():
    """
    set joint label
    :return:
    """
    jnt_list = pm.selected(type='joint')

    if len(jnt_list) == 0:
        print "=JNT= Please make selection. Joint only."

    for jnt in jnt_list:
        split = jnt.split("_")
        jnt.attr('type').set(18)
        if name_data.SIDE_LIST['left'] in split[0]:
            jnt.side.set(1)
            split.pop(0)
        elif name_data.SIDE_LIST['right'] in split[0]:
            jnt.side.set(2)
            split.pop(0)
        elif name_data.SIDE_LIST['middle'] in split[0]:
            jnt.side.set(0)
            split.pop(0)
        else:
            jnt.side.set(0)
        jnt.otherType.set('_'.join(split))


def set_joint_size(val):
    pm.jointDisplayScale(val, a=True)


def create_ik_spline_chain(jnts, prefix='temp', skin_joint=5, forward='x'):
    """
    create stretchy ik spline
    :param forward: forward axis for twist
    :param skin_joint: amount of skin joints
    :param jnts: input, control joints
    :param prefix: name of chain
    :return:
    """
    cons = []
    skn_js = []

    '''groups'''
    util_grp = common.create_name(side='', name=prefix, fn='util', _type='group', create=True)

    con_grp = common.create_name(side='', name=prefix, fn='ctrl', _type='group', create=True)

    jnt_grp = common.create_name(side='', name=prefix, fn='joint', _type='group', create=True)

    ik_jnt_grp = common.create_name(side='', name=prefix, fn='ik_jnt', _type='group', create=True)
    util_grp.addChild(ik_jnt_grp)
    pm.parentConstraint(con_grp, ik_jnt_grp)
    pm.scaleConstraint(con_grp, ik_jnt_grp)

    # find parent
    # prnt = jnts[0].getParent()
    # if not prnt:
    prnt = common.create_name(side='', name=prefix, fn='global_scale', _type='group', create=True)
    util_grp.addChild(prnt)
    pm.scaleConstraint(con_grp, prnt)

    '''ik curve'''
    # create curve from jnts
    ik_crv = common.create_curve(jnts, degree=3, name=common.create_name(side='', name=prefix, _type='ik'))

    # skin curve
    scl = skinning.create_scl(jnts, ik_crv)

    # edit weights
    temp_weights = [w for w in scl.getWeights(ik_crv)]
    weights = []
    for i, w in enumerate(temp_weights):
        if i <= 1:
            weights.append(1.0)
            weights.extend([0.0] * (len(jnts) - 1))
        elif i >= (len(temp_weights) - 2):
            weights.extend([0.0] * (len(jnts) - 1))
            weights.append(1.0)
        else:
            t = [0.0] * (len(jnts) - 1)
            t.insert(i - 1, 1.0)
            weights.extend(t)
    scl.setWeights(ik_crv, range(len(jnts)), weights, False)

    '''cons'''
    con_padding = len(str(len(jnts) + 1))
    for i, j in enumerate(jnts):
        # i = str(len(cons) + 1).zfill(len(str(ik_crv.numCVs())))
        name = common.create_name(side='', name='{}_{}'.format(prefix, str(i + 1).zfill(con_padding)),
                                  fn='ik', _type='joint')
        j.rename(name)
        con_name = j.replace(name_data.TYPE_LIST['joint'], name_data.TYPE_LIST['ctrl'])
        con_struc = shape_gen.create('cube', name=con_name, groups=['nul', 'offset'])
        pm.matchTransform(con_struc[0], j)
        # cj_name = common.create_name(side='', name=prefix, fn='ik' + i, _type='joint')
        # cj = pm.duplicate(jnts[0], po=1, name=cj_name)[0]
        pm.parentConstraint(con_struc[-1], j)

        cons.append(con_struc[-1])
        con_grp.addChild(con_struc[0])

    '''skin joints'''
    padding = len(str(skin_joint + 1))
    dist = ik_crv.length() / (skin_joint - 1.0)
    pm.select(cl=1)
    for sj in range(1, skin_joint + 1):
        name = common.create_name(side='', name='{}_{}'.format(prefix, str(sj).zfill(padding)), fn='skin',
                                  _type='joint')
        j = pm.joint(name=name)
        if sj != 1:
            j.tx.set(dist)

        skn_js.append(j)

    '''ikSpline system'''
    name = common.create_name(side='', name=prefix, _type='ikHandle')
    ik_hdl, eff = pm.ikHandle(name=name, sol='ikSplineSolver', ccv=False, pcv=False, sj=skn_js[0], ee=skn_js[-1],
                              c=ik_crv)

    pm.parent(ik_hdl, ik_crv, util_grp)
    eff.rename(common.create_name(side='', name=prefix, _type='effector'))

    pm.matchTransform(jnt_grp, skn_js[0])
    jnt_grp.addChild(skn_js[0])
    pm.parentConstraint(con_grp, jnt_grp, mo=1)
    pm.scaleConstraint(con_grp, jnt_grp, mo=1)

    # attach twist
    twist_plus = common.create_name(side='', name=prefix, fn='twist', _type='plusMinusAverage', create=True)
    jnts[0].attr('r' + forward).connect(ik_hdl.roll)
    jnts[0].attr('r' + forward).connect(twist_plus.input1D[0])
    jnts[-1].attr('r' + forward).connect(twist_plus.input1D[1])

    # find unitConversion and make it negative
    twist_uc = twist_plus.input1D[0].inputs()[0]
    twist_uc.conversionFactor.set(twist_uc.conversionFactor.get() * -1)
    twist_plus.output1D.connect(ik_hdl.twist)

    # world up vector
    ik_hdl.dTwistControlEnable.set(1)
    ik_hdl.dWorldUpType.set(3)
    jnt_grp.worldMatrix.connect(ik_hdl.dWorldUpMatrix)

    '''stretchy'''
    cons[-1].addAttr('stretchy', at='double', min=0, max=1, dv=1, k=1)
    cons[-1].addAttr('volume_multiplier', at='double', min=-10, max=10, dv=1, k=1)

    s_info = common.create_name(side='', name=prefix, fn='stretchy', _type='curveInfo', create=True)
    ik_crv.worldSpace.connect(s_info.inputCurve)

    norm = common.create_name(side='', name=prefix, fn='stretchy_normalize', _type='multiplyDivide', create=True)
    norm.operation.set(2)
    s_info.arcLength.connect(norm.input1X)
    prnt.sx.connect(norm.input2X)

    s_switch = common.create_name(side='', name=prefix, fn='stretchy_switch', _type='blendColors', create=True)
    norm.outputX.connect(s_switch.color1R)
    s_switch.color2R.set(s_switch.color1R.get())
    cons[-1].stretchy.connect(s_switch.blender)

    factor = common.create_name(side='', name=prefix, fn='stretchy_factor', _type='multiplyDivide', create=True)
    factor.operation.set(2)
    s_switch.outputR.connect(factor.input1X)
    factor.input2X.set(factor.input1X.get())

    vol_mult = common.create_name(side='', name=prefix, fn='stretchy_vol', _type='multiplyDivide', create=True)
    cons[-1].volume_multiplier.connect(vol_mult.input1X)
    vol_mult.input2X.set(.5)

    sqrt = common.create_name(side='', name=prefix, fn='stretchy_sqrt', _type='multiplyDivide', create=True)
    sqrt.operation.set(3)
    factor.outputX.connect(sqrt.input1X)
    vol_mult.outputX.connect(sqrt.input2X)

    invr = common.create_name(side='', name=prefix, fn='stretchy_invr', _type='multiplyDivide', create=True)
    invr.operation.set(2)
    invr.input1X.set(1)
    sqrt.outputX.connect(invr.input2X)

    for j in skn_js[:-1]:
        factor.outputX.connect(j.sx)
        invr.outputX.connect(j.sy)
        invr.outputX.connect(j.sz)

    # new jnt to prevent popping on last joint
    npoc = common.create_name(side='', name=prefix, fn='ik_end', _type='nearestPointOnCurve', create=True)
    ik_crv.worldSpace.connect(npoc.inputCurve)

    j_dcmp = common.create_name(side='', name=prefix, fn='ik_end_pos', _type='decomposeMatrix', create=True)
    skn_js[-1].worldMatrix.connect(j_dcmp.inputMatrix)
    j_dcmp.outputTranslate.connect(npoc.inPosition)

    name = common.create_name(side='', name=prefix, fn='ik_end_pxy', _type='loc')
    end_pxy = shape_gen.create('locator', name=name, groups=[])
    util_grp.addChild(end_pxy)
    npoc.position.connect(end_pxy.t)

    name = skn_js[-1].name()
    skn_js[-1].rename(skn_js[-1].name().replace('skin', name_data.TYPE_LIST['end']))
    end_jnt = pm.duplicate(skn_js[-1], po=1, name=name)[0]
    skn_js[-1].drawStyle.set(2)
    pm.pointConstraint(end_pxy, end_jnt)
    pm.orientConstraint(skn_js[-1], end_jnt)

    # clean up
    pm.parent(jnts, ik_jnt_grp)
    # TODO return data
    return


def create_stretchy_ik(ikh, con=None, forward='x', util_grp=None):
    """
    create stretchy with rotate plane solver ik, 3 joints only
    :return:
    """
    f_at = 't' + forward

    if ikh.type() != 'ikHandle':
        print 'Only accept ikHandle'
        return

    if con is None:
        con = common.create_name(side='', name=ikh.name(), _type='transform', create=True)

    if 'stretchy' not in pm.listAttr(con):
        con.addAttr("stretchy", at="double", min=0, max=1, dv=1, k=1)

    ik_name = pm.ikHandle(ikh, q=1, n=1)
    joint_list = ikh.getJointList()
    # get last joint
    joint_list.append(ikh.getEffector().tx.inputs()[0])

    '''create proxy for joint[0] and joint[-1], to prevent cycle'''
    pxy_a = common.create_name(side='', name=ik_name, fn='pinA', _type='locator', create=True)
    pm.matchTransform(pxy_a, joint_list[0])
    pm.parentConstraint(joint_list[0].getParent(), pxy_a, mo=1)
    pxy_b = common.create_name(side='', name=ik_name, fn='pinB', _type='locator', create=True)
    pm.parentConstraint(ikh, pxy_b)

    pxy_grp = common.create_name(side='', name=ik_name, fn='stretch_pxy', _type='group', create=True)
    pm.parent(pxy_a, pxy_b, pxy_grp)
    if util_grp:
        util_grp.addChild(pxy_grp)

    dist_node = common.create_name(side='', name=ik_name, _type='distanceBetween', create=True)
    pxy_a.worldMatrix.connect(dist_node.inMatrix1)
    pxy_b.worldMatrix.connect(dist_node.inMatrix2)

    '''total distance from joint[0] to [2]'''
    total_dis = (joint_list[0].getTranslation(space='world') - joint_list[1].getTranslation(space='world')).length() + \
                (joint_list[2].getTranslation(space='world') - joint_list[1].getTranslation(space='world')).length()

    '''math node'''
    switch_node1 = common.create_name(side='', name=ik_name, fn='stretch_switch', _type='multiplyDivide', create=True)
    dist_node.distance.connect(switch_node1.i1x)
    con.stretchy.connect(switch_node1.i2x)

    scale_node = common.create_name(side='', name=ik_name, fn='stretch_scaleFix', _type='multiplyDivide', create=True)
    scale_node.operation.set(2)
    switch_node1.outputX.connect(scale_node.i1x)

    '''SDK'''
    anim_crvs = []
    for jnt in joint_list[1:]:
        pm.setDrivenKeyframe('{}.{}'.format(jnt, f_at), cd=dist_node + ".distance", dv=total_dis,
                             v=(pm.getAttr('{}.{}'.format(jnt, f_at))), itt="linear", ott="linear")
        pm.setDrivenKeyframe('{}.{}'.format(jnt, f_at), cd=dist_node + ".distance", dv=total_dis * 2,
                             v=(pm.getAttr('{}.{}'.format(jnt, f_at)) * 2), itt="linear", ott="linear")

        anim_crv = pm.PyNode('{}.{}'.format(jnt, f_at)).inputs(type="animCurve")[0]
        anim_crv.postInfinity.set(4)
        scale_node.outputX.connect(anim_crv.input, f=1)
        anim_crvs.append(anim_crv)

    '''get pv_con'''
    pv_const = pm.poleVectorConstraint(ikh, q=1)
    pv_con = None
    if pv_const:
        pv_con = pm.PyNode(pv_const).getTargetList()[0]

    '''pin system'''
    if pv_con:
        if 'pin' in pm.listAttr(pv_con, ud=1):
            print '==Stretchy== Unable to create "pin" attribute. Aborted on create pin system.'
            return
        pv_con.addAttr('pin', min=0, max=1, k=1, dv=0)

        dist_node_a = common.create_name(side='', name=ik_name, fn='A', _type='distanceBetween', create=True)
        pxy_a.worldMatrix.connect(dist_node_a.inMatrix1)
        pv_con.worldMatrix.connect(dist_node_a.inMatrix2)

        dist_node_b = common.create_name(side='', name=ik_name, fn='B', _type='distanceBetween', create=True)
        pxy_b.worldMatrix.connect(dist_node_b.inMatrix1)
        pv_con.worldMatrix.connect(dist_node_b.inMatrix2)

        pin_scale_node = common.create_name(side='', name=ik_name, fn='pin_scaleFix', _type='multiplyDivide',
                                            create=True)
        pin_scale_node.operation.set(2)
        dist_node_a.distance.connect(pin_scale_node.i1x)
        dist_node_b.distance.connect(pin_scale_node.i1z)

        blend_node = common.create_name(side='', name=ik_name, fn='stretchy', _type='blendColors', create=True)
        anim_crvs[0].output.connect(blend_node.color2R)
        anim_crvs[1].output.connect(blend_node.color2B)

        # if translate value is negative value
        if pm.getAttr('{}.{}'.format(joint_list[1], f_at)) < 0:
            neg_node = common.create_name(side='', name=ik_name, fn='pin_negate', _type='multiplyDivide', create=True)
            neg_node.i2.set([-1, -1, -1])
            pin_scale_node.outputX.connect(neg_node.i1x)
            pin_scale_node.outputZ.connect(neg_node.i1z)
            neg_node.output.connect(blend_node.color1)
        else:
            pin_scale_node.outputX.connect(blend_node.color1R)
            pin_scale_node.outputZ.connect(blend_node.color1B)

        blend_node.outputR.connect(joint_list[1].attr(f_at), f=1)
        blend_node.outputB.connect(joint_list[2].attr(f_at), f=1)
        pv_con.pin.connect(blend_node.blender)

    '''length multiplier'''
    con.addAttr('upperLength', at='double', dv=1, k=1)
    con.upperLength.connect(joint_list[0].attr('s'+forward))

    con.addAttr('lowerLength', at='double', dv=1, k=1)
    con.lowerLength.connect(joint_list[1].attr('s' + forward))

    pm.select(ikh, con)
    return scale_node


class create_RpIk:
    # TODO continue create class, add stretch & pin pv, util grp
    def __init__(self, objs, pv_dist=1):
        self.sj = objs[0]
        self.mj = objs[1]
        self.ej = objs[2]
        self.pv_dist = pv_dist

        self.name = common.replace_name(self.sj.name(), 'joint', '')
        if self.name.endswith('_'):
            self.name = self.name[:-1]

        # trim ik string
        if '_ik' in self.name.lower():
            for iks in ['_ik', '_IK']:
                self.name.replace(iks, '')

        self._create()

    def _create(self):
        self.ik_root = pm.spaceLocator(name=common.create_name(side='', name=self.name, fn='ik', _type='root'))
        pm.matchTransform(self.ik_root, self.sj, pos=1)

        # check sj parent
        if not self.sj.getParent():
            grp = common.group_pivot(self.sj, layer=['ofs'])
            pm.parentConstraint(self.ik_root, grp, mo=1)
        else:
            pm.parentConstraint(self.sj.getParent(), self.ik_root, mo=1)
            pm.parentConstraint(self.ik_root, self.sj, mo=1)

        self.ikh, eff = pm.ikHandle(sol='ikRPsolver', sj=self.sj, ee=self.ej,
                                    name=common.create_name(side='', name=self.name, _type='ikHandle'))
        self.ikh_grp = common.group_pivot(self.ikh, layer=['ofs'])[0]
        eff.rename(common.create_name(side='', name=self.name, _type='effector'))

        self.ik_con = pm.spaceLocator(name=common.create_name(side='', name=self.name, fn='ik', _type='proxy'))
        ik_prnt = common.group_pivot(self.ik_con, layer=['ofs'])[0]
        pm.matchTransform(ik_prnt, self.ej)
        pm.parentConstraint(self.ik_con, self.ikh_grp, mo=1)
        pm.orientConstraint(self.ik_con, self.ej, mo=1)

        self.pv_con = pm.spaceLocator(name=common.create_name(side='', name=self.name, fn='pv', _type='proxy'))
        self.pv_con.t.set(self.get_pv())
        pm.poleVectorConstraint(self.pv_con, self.ikh)

        temp_name = common.replace_name(self.ik_con.name(), 'proxy', 'util')
        self.util_grp = common.create_name(side='', name=temp_name, _type='group', create=True)
        pm.parent(self.ikh_grp, ik_prnt, self.pv_con, self.ik_root, self.util_grp)

        self.global_scale = create_stretchy_ik(self.ikh, con=self.ik_con, util_grp=self.util_grp)

    def get_pv(self):
        pos = find_pv([self.sj, self.mj, self.ej], multiplier=6 * self.pv_dist)
        return [round(q, 4) for q in pos]

    def delete_loc_shape(self):
        for obj in [self.ik_root, self.ik_con, self.pv_con]:
            if obj.getShapes():
                pm.delete(obj.getShapes())

    def lock_locs(self):
        channels.cb_status([self.ik_root, self.ik_con, self.pv_con], all=1, lock=True, show=False)

    @staticmethod
    def copy_attr(src, target):
        attributes.duplicate_attrs([src, target], bridge_mode=False)
        for at in src.listAttr(ud=1):
            if at.isSettable:
                target.attr(at.attrName()).connect(at)


def duplicate_chain(jnts, old_value, new_value):
    """
    duplicate joint chain. Append new_value if old_value is not in the name
    :param jnts:
    :param old_value: string need to be replaced
    :param new_value:  replace string
    :return:
    """
    new_jnts = []
    for jnt in jnts:
        new_name = jnt.replace(old_value, new_value)
        if old_value not in jnt.name():
            new_name = '{}_{}'.format(jnt, new_value)
        nj = pm.duplicate(jnt, name=new_name, po=1)[0]
        if new_jnts:
            new_jnts[-1].addChild(nj)
        new_jnts.append(nj)
    return new_jnts


def blend_chain(jnts, replace_key='JNT', suffix=None):
    """
    Attach two chains to given chain
    :param jnts: all joint in single chain
    :param replace_key:
    :param suffix: [result suffix, ik suffix, fk suffix]
    :return:
    """
    if suffix is None:
        suffix = ['JNT', 'IKJ', 'FKJ']

    jnts_a = []
    jnts_b = []
    sys_grp = create_name(side='', name=jnts[0], fn='sys', _type='group', create=True)
    sys_grp.addAttr('fkIk', at='double', min=0, max=1, k=1)
    sys_grp.addAttr('fkVis', at='double', min=0, max=1, k=1)
    sys_grp.addAttr('ikVis', at='double', min=0, max=1, k=1)
    vis_rev_node = create_name(side='', name=jnts[0], fn='fkikVis', _type='reverse', create=True)
    sys_grp.fkIk.connect(vis_rev_node.inputX)
    vis_rev_node.inputX.connect(sys_grp.ikVis)
    vis_rev_node.outputX.connect(sys_grp.fkVis)

    if jnts[0].getParent():
        pm.parentConstraint(jnts[0].getParent(), sys_grp)
        pm.scaleConstraint(jnts[0].getParent(), sys_grp)
    else:
        offset_grp = create_name(side='', name=jnts[0], fn='offset', _type='group', create=True)
        pm.delete(pm.parentConstraint(jnts[0], offset_grp))
        offset_grp.addChild(jnts[0])
        pm.parentConstraint(offset_grp, sys_grp)
        pm.scaleConstraint(offset_grp, sys_grp)

    for jnt in jnts:
        if replace_key and replace_key in jnt.name():
            new_name = jnt.replace(replace_key, "{}")
        else:
            new_name = jnt.name() + "_{}"

        jnt.rename(new_name.format(suffix[0]))
        new_ja = pm.duplicate(jnt, name=new_name.format(suffix[1]), po=1)[0]
        if jnts_a:
            jnts_a[-1].addChild(new_ja)
        else:
            sys_grp.addChild(new_ja)
            sys_grp.ikVis.connect(new_ja.v)
        jnts_a.append(new_ja)

        new_jb = pm.duplicate(jnt, name=new_name.format(suffix[2]), po=1)[0]
        if jnts_b:
            jnts_b[-1].addChild(new_jb)
        else:
            sys_grp.addChild(new_jb)
            sys_grp.fkVis.connect(new_jb.v)
        jnts_b.append(new_jb)

        for at in 'trs':
            switch_node = create_name(side='', name=jnt, fn=atName[at], _type='blendColors', create=True)
            sys_grp.fkIk.connect(switch_node.blender)
            new_ja.attr(at).connect(switch_node.color1)
            new_jb.attr(at).connect(switch_node.color2)
            switch_node.output.connect(jnt.attr(at))

    return {'IK': jnts_a, 'FK': jnts_b, 'result': jnts, 'sys': sys_grp}

