import pymel.all as pm

from ..utils import common
from ..utils import joints
from ..utils import channels
from ..tools.controllerShape import main as shape_gen

reload(common)
reload(joints)
reload(channels)
reload(shape_gen)
# TODO: quad mode?

def rig_leg_ik(jnts, biped=True, quad=False, mirror=False, scale=1):
    """
    :param jnts: [hip, leg, knee, ankle, foot, toe]
    :param biped: make ik con on ankle
    :param quad: make ik con on foot
    :param mirror:
    :return:
    """

    # create ik con
    side = 'left' if jnts[0].name().split('_')[0].lower() == 'l' else 'right'
    leg_name = common.replace_name(jnts[1].name(), 'joint', '')
    knee_name = common.replace_name(jnts[2].name(), 'joint', '')
    ik_con_list = shape_gen.create('square', name='{}{}'.format(leg_name, common.TYPE_LIST['ctrl']),
                                   groups=['offset', 'constraint', 'mirror'], color=side)
    ik_con = ik_con_list[-1]
    # resize
    pm.move(ik_con.cv, 0, 0, .5, os=1, r=1)
    pm.scale(ik_con.cv, scale, scale, scale, os=1, r=1)

    # make ik con on ground and aim at foot
    if biped:
        pm.matchTransform(ik_con_list[0], jnts[3])
        ik_con_list[0].ty.set(0)
        pm.delete(pm.aimConstraint(jnts[3], ik_con_list[0], aimVector=[0, 0, 1], upVector=[0, 1, 0]))
        ik_con_list[0].rx.set(0)
        ik_con_list[0].rz.set(0)
    else:
        pm.matchTransform(ik_con_list[0], jnts[4])
        pm.delete(pm.aimConstraint(jnts[4], ik_con_list[0], aimVector=[0, 0, 1], upVector=[0, 1, 0]))
        ik_con_list[0].rx.set(0)
        ik_con_list[0].rz.set(0)

    if mirror:
        ik_con_list[2].sx.set(-1)

    # attributes
    ik_con.addAttr('roll', at='double', dv=0, k=1)
    ik_con.addAttr('rollHeight', at='double', dv=60, k=1)
    ik_con.addAttr('ballYaw', at='double', dv=0, k=1)
    ik_con.addAttr('toeTap', at='double', dv=0, k=1)
    ik_con.addAttr('toeTipYaw', at='double', dv=0, k=1)
    ik_con.addAttr('toeTipPitch', at='double', dv=0, k=1)
    ik_con.addAttr('bank', at='double', dv=0, k=1)
    ik_con.addAttr('footYaw', at='double', dv=0, k=1)
    ik_con.addAttr('heelYaw', at='double', dv=0, k=1)
    ik_con.addAttr('heelPitch', at='double', dv=0, k=1)

    # space for ik
    ik_con_space_grp = common.create_space_attr(ik_con_list[1], parents=[jnts[0], 'm_root_jnt', 'world'],
                                                nice_name=['hip', 'root', 'world'], con=ik_con)

    # create pole vector con
    pv_con_list = shape_gen.create('pyramid', name='{}{}'.format(knee_name, common.TYPE_LIST['ctrl']),
                                   groups=['offset', 'constraint', 'mirror'], color=side)
    pos = joints.find_pv(jnts[1:4], multiplier=5)
    pv_con_list[0].t.set(pos)
    pv_con_list[-1].rx.set(-90)
    pm.makeIdentity(pv_con_list[-1], a=1, r=1)

    if mirror:
        pv_con_list[2].sx.set(-1)

    # resize
    pm.move(pv_con_list[-1].cv, 0, 0, 1, os=1, r=1)
    pm.scale(pv_con_list[-1].cv, scale*.8, scale*.8, scale*.8, os=1, r=1)

    pv_con_space_grp = common.create_space_attr(pv_con_list[1],
                                                parents=[ik_con, jnts[0], 'm_root_jnt', 'world'],
                                                nice_name=['ik_con', 'hip', 'root', 'world'], con=pv_con_list[-1])

    # find & create locators
    ik_con.addAttr('pivotCtrlVis', at='double', min=0, max=1, dv=0, k=1)
    piv_grp = common.create_name(side='', name=leg_name[:-1], fn='piv', _type='group', create=True, find=True)
    ik_con.pivotCtrlVis.connect(piv_grp.v)
    piv_name = ['bankIn', 'bankOut', 'toeTip', 'heel', 'foot']
    piv_locs = []
    for piv in piv_name:
        loc = common.create_name(side='', name='{}_{}'.format(leg_name, piv), fn='piv',
                                 _type='locator', create=True, find=True)
        piv_grp.addChild(loc)
        piv_locs.append(loc)

    ik_con.addChild(piv_grp)
    pm.matchTransform(piv_grp, ik_con)
    piv_grp.s.set([1] * 3)

    """bank in/ out"""
    piv_locs[0].tx.set(-1.5)
    bank_in_grp = common.create_name(side='', name='{}_bankIn'.format(leg_name[:-1]), fn='driven', _type='group',
                                     create=True)
    # pivot
    pm.matchTransform(bank_in_grp, ik_con)
    piv_locs[0].t.connect(bank_in_grp.rotatePivot)
    piv_locs[0].t.connect(bank_in_grp.scalePivot)
    ik_con.addChild(bank_in_grp)

    # driver
    bank_in_cond = common.create_name(side='', name='{}_bankIn'.format(leg_name[:-1]), _type='condition',
                                      create=True)
    bank_in_cond.operation.set(4 if not mirror else 2)
    ik_con.bank.connect(bank_in_cond.firstTerm)
    ik_con.bank.connect(bank_in_cond.colorIfFalseR)
    bank_in_cond.outColorR.connect(bank_in_grp.rz)

    piv_locs[1].tx.set(1.5)
    bank_out_grp = common.create_name(side='', name='{}_bankOut'.format(leg_name[:-1]), fn='driven', _type='group',
                                      create=True)
    # pivot
    pm.matchTransform(bank_out_grp, ik_con)
    piv_locs[1].t.connect(bank_out_grp.rotatePivot)
    piv_locs[1].t.connect(bank_out_grp.scalePivot)

    bank_in_grp.addChild(bank_out_grp)

    # driver
    bank_out_cond = common.create_name(side='', name='{}_bankOut'.format(leg_name[:-1]), _type='condition',
                                       create=True)
    bank_out_cond.operation.set(2 if not mirror else 4)
    ik_con.bank.connect(bank_out_cond.firstTerm)
    ik_con.bank.connect(bank_out_cond.colorIfFalseR)
    bank_out_cond.outColorR.connect(bank_out_grp.rz)

    """ankle point on ground"""
    pm.matchTransform(piv_locs[-1], jnts[3], pos=1)
    piv_locs[-1].ty.set(0)
    foot_grp = common.create_name(side='', name='{}_foot'.format(leg_name[:-1]), _type='group', create=True)

    # pivot
    bank_out_grp.addChild(foot_grp)
    pm.matchTransform(foot_grp, ik_con)
    piv_locs[-1].t.connect(foot_grp.rotatePivot)
    piv_locs[-1].t.connect(foot_grp.scalePivot)
    piv_locs[-1].t.connect(ik_con.rotatePivot)
    piv_locs[-1].t.connect(ik_con.scalePivot)

    ik_con.footYaw.connect(foot_grp.ry)

    """heel"""
    piv_locs[-2].tz.set(-1.5)
    heel_con_list = shape_gen.create('cube', name='{}heel_{}'.format(leg_name, common.TYPE_LIST['ctrl']),
                                     groups=['offset', 'driven'], color=side)
    foot_grp.addChild(heel_con_list[0])

    # pivot
    for con in heel_con_list:
        piv_locs[-2].t.connect(con.rotatePivot)
        piv_locs[-2].t.connect(con.scalePivot)
        con.t.set([0] * 3)
        con.r.set([0] * 3)
        con.s.set([1] * 3)

    # resize
    pm.move(heel_con_list[-1].cv, piv_locs[-2].tx.get(), piv_locs[-2].ty.get(), piv_locs[-2].tz.get(), r=1)
    pm.scale(heel_con_list[-1].cv, scale*.35, scale*.35, scale*.35, os=1, r=1)

    roll_neg_cond = common.create_name(side='', name='{}_neg_roll'.format(leg_name[:-1]), _type='condition',
                                       create=True)
    roll_neg_cond.operation.set(4)
    ik_con.roll.connect(roll_neg_cond.firstTerm)
    ik_con.roll.connect(roll_neg_cond.colorIfTrueR)
    roll_neg_cond.colorIfFalse.set([0]*3)

    heel_rot_sum = common.create_name(side='', name='{}_rot_drn'.format(leg_name[:-1]), _type='plusMinusAverage',
                                      create=True)
    ik_con.heelPitch.connect(heel_rot_sum.input3D[0].input3Dx)
    ik_con.heelYaw.connect(heel_rot_sum.input3D[0].input3Dy)
    roll_neg_cond.outColorR.connect(heel_rot_sum.input3D[1].input3Dx)
    heel_rot_sum.output3D.connect(heel_con_list[1].r)

    """toe tip"""
    pm.matchTransform(piv_locs[2], jnts[-1], pos=1)
    piv_locs[2].ty.set(0)

    tt_con_list = shape_gen.create('cube', name='{}toeTip_{}'.format(leg_name, common.TYPE_LIST['ctrl']),
                                   groups=['offset', 'driven'], color=side)

    heel_con_list[-1].addChild(tt_con_list[0])

    # pivot
    for con in tt_con_list:
        piv_locs[2].t.connect(con.rotatePivot)
        piv_locs[2].t.connect(con.scalePivot)
        con.t.set([0] * 3)
        con.r.set([0] * 3)
        con.s.set([1] * 3)

    # resize
    pm.move(tt_con_list[-1].cv, piv_locs[2].tx.get(), piv_locs[2].ty.get(), piv_locs[2].tz.get(), r=1)
    pm.scale(tt_con_list[-1].cv, scale*.35, scale*.35, scale*.35, os=1, r=1)

    # add sub
    tt_con_list.extend(shape_gen.create_sub_ctrl([tt_con_list[-1]]))
    piv_locs[2].t.connect(tt_con_list[-1].rotatePivot)
    piv_locs[2].t.connect(tt_con_list[-1].scalePivot)

    tt_drn_sum = common.create_name(side='', name='{}_max_roll'.format(leg_name[:-1]), _type='plusMinusAverage',
                                    create=True)
    ik_con.toeTipPitch.connect(tt_drn_sum.input3D[0].input3Dx)
    ik_con.toeTipYaw.connect(tt_drn_sum.input3D[0].input3Dy)
    tt_drn_sum.output3D.connect(tt_con_list[1].r)

    """toe"""
    toe_con_list = shape_gen.create('circle', name='{}toe_{}'.format(leg_name, common.TYPE_LIST['ctrl']),
                                    groups=['offset', 'driven'], color=side)
    tt_con_list[-1].addChild(toe_con_list[0])
    pm.matchTransform(toe_con_list[0], jnts[4], pos=1)
    toe_con_list[0].s.set([1] * 3)
    pm.rotate(toe_con_list[-1].cv, 90, 0, 0, os=1, r=1)

    # resize
    pm.move(toe_con_list[-1].cv, 0, 0, scale, os=1, r=1)
    pm.scale(toe_con_list[-1].cv, scale, scale, scale, os=1, r=1)

    # driven
    ik_con.ballYaw.connect(toe_con_list[0].ry)
    ik_con.toeTap.connect(toe_con_list[1].rx)

    """ball"""
    ball_con_list = shape_gen.create('cube', name='{}ball_{}'.format(leg_name, common.TYPE_LIST['ctrl']),
                                     groups=['offset', 'driven'], color=side)

    toe_con_list[0].addChild(ball_con_list[0])
    pm.matchTransform(ball_con_list[0], jnts[4], pos=1)
    ball_con_list[0].r.set([0] * 3)
    ball_con_list[0].s.set([1] * 3)

    # resize
    pm.scale(ball_con_list[-1].cv, scale*.35, scale*.35, scale*.35, os=1, r=1)

    # roll & roll height
    roll_pos_cond = common.create_name(side='', name='{}_pos_roll'.format(leg_name[:-1]), _type='condition',
                                       create=True)
    roll_pos_cond.operation.set(2)
    ik_con.roll.connect(roll_pos_cond.firstTerm)
    ik_con.roll.connect(roll_pos_cond.colorIfTrueR)
    roll_pos_cond.colorIfFalse.set([0] * 3)

    roll_heig_mult = common.create_name(side='', name='{}_roll_height'.format(leg_name[:-1]), _type='multiplyDivide',
                                        create=True)
    ik_con.rollHeight.connect(roll_heig_mult.i1x)
    roll_heig_mult.i2x.set(2)

    roll_heig_sr = common.create_name(side='', name='{}_roll_height'.format(leg_name[:-1]), _type='setRange',
                                      create=True)
    roll_heig_sr.minX.set(1)
    roll_heig_mult.i1x.connect(roll_heig_sr.oldMinX)
    roll_heig_mult.outputX.connect(roll_heig_sr.oldMaxX)
    roll_pos_cond.outColorR.connect(roll_heig_sr.valueX)

    roll_pos_mult = common.create_name(side='', name='{}_pos_roll'.format(leg_name[:-1]), _type='multiplyDivide',
                                       create=True)
    roll_pos_cond.outColorR.connect(roll_pos_mult.i1x)
    roll_heig_sr.outValueX.connect(roll_pos_mult.i2x)
    roll_pos_mult.outputX.connect(ball_con_list[1].rx)

    # roll max on toe tip
    roll_max_sum = common.create_name(side='', name='{}_max_roll'.format(leg_name[:-1]), _type='plusMinusAverage',
                                      create=True)
    roll_max_sum.operation.set(2)
    roll_pos_cond.outColorR.connect(roll_max_sum.input1D[0])
    roll_heig_mult.i1x.connect(roll_max_sum.input1D[1])

    roll_max_cond = common.create_name(side='', name='{}_max_roll'.format(leg_name[:-1]), _type='condition',
                                       create=True)
    roll_max_cond.operation.set(2)
    roll_pos_cond.outColorR.connect(roll_max_cond.firstTerm)
    roll_heig_mult.i1x.connect(roll_max_cond.secondTerm)
    roll_max_sum.output1D.connect(roll_max_cond.colorIfTrueR)
    roll_max_cond.colorIfFalse.set([0] * 3)

    roll_max_cond.outColorR.connect(tt_drn_sum.input3D[1].input3Dx)

    '''ik handles'''
    leg_ik_sys = joints.Create_RpIk(jnts[1:4])
    leg_ik_sys.delete_loc_shape()
    pm.parent(leg_ik_sys.ik_con.getParent(), ball_con_list[-1])
    ik_con.addAttr('stretchyAttr', at='enum', en='____:', k=1)
    ik_con.stretchyAttr.set(l=1)
    leg_ik_sys.copy_attr(leg_ik_sys.ik_con, ik_con)

    pm.parent(leg_ik_sys.pv_con, pv_con_list[-1])
    pm.matchTransform(leg_ik_sys.pv_con, pv_con_list[-1])
    leg_ik_sys.copy_attr(leg_ik_sys.pv_con, pv_con_list[-1])

    leg_ik_sys.lock_locs()

    ankle_ikh = pm.ikHandle(name=common.replace_name(jnts[3].name(), 'joint', 'ikHandle'), sol='ikRPsolver',
                            sj=jnts[3], ee=jnts[4])
    ankle_ikh[1].rename(ankle_ikh[0].name().replace('ikHandle', 'effector'))
    ankle_ikh_grp = common.group_pivot(ankle_ikh[0], layer=['offset'])
    leg_ik_sys.ikh_grp.addChild(ankle_ikh_grp[0])

    ball_ikh = pm.ikHandle(name=common.replace_name(jnts[4].name(), 'joint', 'ikHandle'), sol='ikRPsolver',
                           sj=jnts[4], ee=jnts[5])
    ball_ikh[1].rename(ball_ikh[0].name().replace('ikHandle', 'effector'))
    ball_ikh_grp = common.group_pivot(ball_ikh[0], layer=['offset'])
    pm.parentConstraint(toe_con_list[-1], ball_ikh_grp[0], mo=1)
    leg_ik_sys.util_grp.addChild(ball_ikh_grp[0])

    # lock attr
    channels.cb_status([ik_con], v=1, lock=1, show=False)
    channels.cb_status([pv_con_list[-1]], rotates='xyz', v=1, lock=1, show=False)
    channels.cb_status([tt_con_list[-2], heel_con_list[-1]], scales='xyz', v=1, lock=1, show=False)
    channels.cb_status([toe_con_list[-1], ball_con_list[-1]], translates='xyz', scales='xyz', v=1, lock=1, show=False)

    pass
