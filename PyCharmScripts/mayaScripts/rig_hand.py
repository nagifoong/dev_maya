import pymel.all as pm

from ..utils import common
from ..tools.controllerShape import main as shape_gen

reload(common)
reload(shape_gen)


# TODO mirror function

def create_hand_rig(jnts, mid_pos=[0, 1], side='l', name=None, attach_to=None, thumb=None, con_scale=1, mirror=False):
    """
    Create hand rig with provided jnts
    :param mirror: mirror behavior on ctrls
    :param con_scale: scale of ctrls
    :param thumb: [thumb joints]
    :param jnts: [every first joint of the chain]. *Exclude thumb
    :param mid_pos: mid position of fingers for spreading and cup
    :param side: side prefix
    :param name: name of chain
    :param attach_to: attach to this object
    :return:
    """
    if min(mid_pos) < 0 or max(mid_pos) > len(jnts) or not isinstance(mid_pos, list):
        print '==HANDS== Invalid mid_pos.'
        return

    # attach
    if not attach_to:
        attach_to = common.create_name(side=side, name=name, fn='attach_proxy', _type='locator', create=True)
        if jnts[0].getParent():
            prnt = jnts[0].getParent()
            pm.parentConstraint(prnt, attach_to)
            pm.scaleConstraint(prnt, attach_to)

    # variables
    if not side:
        side = jnts[0].split('_')[0]

    if len(mid_pos) > 1:
        div = len(jnts) - min(mid_pos) - 1.0
    else:
        div = float(len(jnts) - mid_pos[0])

    div = 1 if div <= 0 else div
    ssc = 0
    cons = {}
    mir_rot = [180, 0, 0]
    mir_scale = [-1, 1, 1]
    aim_v = [1, 0, 0] if not mirror else [-1, 0, 0]
    up_v = [0, 1, 0] if not mirror else [0, -1, 0]

    '''Main groups'''
    main_ctrl_grp = common.create_name(side=side, name=name, fn='finger_main', _type='group', create=True)
    pm.parentConstraint(attach_to, main_ctrl_grp)
    pm.scaleConstraint(attach_to, main_ctrl_grp)

    util_grp = common.create_name(side=side, name=name, fn='finger_util', _type='group', create=True)
    pm.parentConstraint(attach_to, util_grp)
    pm.scaleConstraint(attach_to, util_grp)

    # main util grp
    if pm.ls('util_grp'):
        pm.parent(util_grp, 'util_grp')
    else:
        common.create_name(side='', name='util', _type='group', create=True).addChild(util_grp)

    """Main ctrl"""
    if name:
        side = '{}_{}'.format(side, name)
    temp_name = common.create_name(side=side, name='all_finger', fn='ctrl', _type=None)
    main_con_dict = shape_gen.create('cube', name=temp_name, groups=['offset', 'mirror'])
    main_con = main_con_dict[-1]

    # mirror
    if mirror:
        main_con_dict[1].r.set(mir_rot)
        main_con_dict[1].s.set(mir_scale)

    # con scale
    main_con.s.set([con_scale] * 3)
    pm.makeIdentity(main_con, s=1, a=1)

    # reposition controller
    if len(mid_pos) > 1:
        pm.delete(pm.parentConstraint([jnts[i] for i in mid_pos], main_con_dict[0]))
    else:
        pm.delete(pm.parentConstraint(jnts[mid_pos[0]], main_con_dict[0]))

    main_ctrl_grp.addChild(main_con_dict[0])

    # reposition shape
    loc = pm.spaceLocator()
    loc_grp = pm.group()
    pm.matchTransform(loc_grp, main_con)
    pm.aimConstraint(jnts[-1], loc_grp, aimVector=[1, 0, 0], upVector=[0, 1, 0])
    # pm.makeIdentity(loc)
    pm.matchTransform(loc, jnts[-1])
    loc.t.set([q * 2 for q in loc.t.get()])
    common.move_shape([main_con, loc])
    pm.delete(loc_grp)

    """locators"""
    static_loc = common.create_name(side=side, name=name, fn='static', _type='locator', create=True)
    move_loc = common.create_name(side=side, name=name, fn='move', _type='locator', create=True)
    loc_grps = common.group_pivot(static_loc, layer=['offset'])
    loc_grps[-1].addChild(move_loc)

    util_grp.addChild(loc_grps[0])

    # constrain
    pm.delete(pm.parentConstraint(main_con, loc_grps[0]))
    pm.parentConstraint(main_con, move_loc)

    # attributes
    main_con.addAttr('extra', at='enum', en="___:", k=1)
    main_con.extra.set(l=1)

    extra_at = ['fist', 'spread', 'scrunch']

    # thumb
    if thumb:
        main_con.addAttr('thumb_cup', at='double', min=-10, max=10, dv=0, k=1)
        for at in extra_at:
            main_con.addAttr('thumb_' + at, at='double', min=-10, max=10, dv=0, k=1)

    for at in extra_at:
        main_con.addAttr(at, at='double', min=-10, max=10, dv=0, k=1)

    # multiplier fot extra
    mult_at = []
    for jnt in jnts:
        at_name = "_".join([s for s in jnt.getChildren()[0].split('_') if s in jnt.name() and s != side]) + '_mult'
        main_con.addAttr(at_name, at='double', dv=1, k=1)
        mult_at.append(main_con.attr(at_name))

    """fingers system"""
    main_con.addAttr('fingerFollow', at='enum', en="___:", k=1)
    main_con.fingerFollow.set(l=1)
    ite = 1
    if len(mid_pos) == 1:
        mid_pos = [mid_pos[0] - 1]
    for ind, jnt in enumerate(jnts):
        j_name = common.replace_name(jnt.name(), 'joint', '')
        # remove "_"
        j_name = j_name[:-1]

        if ind > min(mid_pos):
            val = ite / div
            ite += 1
        else:
            val = 0

        # follow attribute
        at_name = '{}_follow'.format(j_name)
        main_con.addAttr(at_name, at='double', min=0, max=100, dv=val * 100, k=1)
        follow_uc = common.create_name(side='', name=j_name, _type='unitConversion', create=True)
        follow_uc.conversionFactor.set(.01)
        main_con.attr(at_name).connect(follow_uc.input)
        follow_rev = common.create_name(side='', name=j_name, _type='reverse', create=True)
        follow_uc.output.connect(follow_rev.inputX)
        follow_uc.output.connect(follow_rev.inputY)
        follow_uc.output.connect(follow_rev.inputZ)

        follow_mult = common.create_name(side='', name=j_name, _type='multiplyDivide', create=True)
        move_loc.r.connect(follow_mult.input1)
        follow_rev.input.connect(follow_mult.input2)

        # locator
        loc = common.create_name(side='', name=j_name, _type='locator', create=True)
        loc_grps[-1].addChild(loc)
        pm.delete(pm.parentConstraint(static_loc, loc))
        # pm.delete(pm.parentConstraint(jnt, loc))
        const = pm.pointConstraint(static_loc, move_loc, loc, mo=1)
        attrs = const.getWeightAliasList()
        follow_rev.inputX.connect(attrs[1])
        follow_rev.outputX.connect(attrs[0])

        # create controller
        drn_suf = common.TYPE_LIST['driven']
        j_con_dict = shape_gen.create('sphere', name=common.replace_name(jnt.name(), 'joint', 'ctrl'),
                                      groups=['offset', 'constraint', 'cup_{}'.format(drn_suf), 'driven'])
        # mirror
        if mirror:
            j_con_dict[1].r.set(mir_rot)
            j_con_dict[1].s.set(mir_scale)

        # con scale
        j_con_dict[-1].s.set([con_scale] * 3)
        pm.makeIdentity(j_con_dict[-1], s=1, a=1)

        cons[jnt] = [j_con_dict[-1]]
        main_ctrl_grp.addChild(j_con_dict[0])
        pm.delete(pm.parentConstraint(jnt, j_con_dict[0]))
        pm.pointConstraint(loc, j_con_dict[1], mo=1)
        pm.xform(j_con_dict[2], ws=1, piv=pm.xform(loc, q=1, ws=1, piv=1)[:3])
        follow_mult.outputX.connect(j_con_dict[2].rx)
        follow_mult.outputY.connect(j_con_dict[3].ry)
        follow_mult.outputZ.connect(j_con_dict[3].rz)

        for c in j_con_dict:
            c.ro.set(2)

        pm.parentConstraint(j_con_dict[-1], jnt, mo=1)
        j_con_dict[-1].s.connect(jnt.s)
        # pm.scaleConstraint(j_con_dict[-1], jnt, mo=1)
        # for spread
        spread_loc = pm.spaceLocator()
        pm.delete(pm.parentConstraint([jnts[i].getChildren(ad=1)[0] for i in mid_pos], spread_loc))
        spread_aim = pm.spaceLocator()
        spread_aim_grp = pm.group()

        pm.aimConstraint(spread_loc, spread_aim, aimVector=aim_v, upVector=up_v)

        # ssc
        jnt.ssc.set(ssc)
        [ad_j.ssc.set(ssc) for ad_j in jnt.getChildren(ad=1, type='joint')]

        # chain children joint, always skip last one
        ad_jnts = jnt.getChildren(ad=1, type='joint')[::-1]
        for i, ad_j in enumerate(ad_jnts[:-1]):
            if i == 0:
                grps = ['offset', 'constraint', 'cup_{}'.format(drn_suf), 'driven']
            else:
                grps = ['offset', 'constraint', 'driven']
            ad_con_dict = shape_gen.create('sphere', name=common.replace_name(ad_j.name(), 'joint', 'ctrl'),
                                           groups=grps)
            pm.matchTransform(ad_con_dict[0], ad_j)

            # mirror
            if mirror:
                ad_con_dict[1].r.set(mir_rot)
                ad_con_dict[1].s.set(mir_scale)

            # con scale
            ad_con_dict[-1].s.set([con_scale] * 3)
            pm.makeIdentity(ad_con_dict[-1], s=1, a=1)

            for c in ad_con_dict:
                c.ro.set(2)

            pm.parentConstraint(ad_con_dict[-1], ad_j)
            ad_con_dict[-1].s.connect(ad_j.s)
            # pm.scaleConstraint(ad_con_dict[-1], ad_j)
            cons[jnt][-1].addChild(ad_con_dict[0])
            cons[jnt].append(ad_con_dict[-1])

            # extra driven
            ad_j_name = common.replace_name(ad_j.name(), 'joint', '')[:-1]
            drn_plus = common.create_name(side='', name=ad_j_name, fn='driven', _type='plusMinusAverage', create=True)
            # drn_plus.output3D.connect(ad_con_dict[1].r)

            # fist
            pm.setDrivenKeyframe(drn_plus.input3D[0].input3Dz, cd=main_con.fist, dv=0, v=0)
            pm.setDrivenKeyframe(drn_plus.input3D[0].input3Dz, cd=main_con.fist, dv=10, v=-90)
            pm.setDrivenKeyframe(drn_plus.input3D[0].input3Dz, cd=main_con.fist, dv=-10, v=90)

            # scrunch
            sdk_val = -90 if i == 0 else 90
            pm.setDrivenKeyframe(drn_plus.input3D[1].input3Dz, cd=main_con.scrunch, dv=0, v=0)
            pm.setDrivenKeyframe(drn_plus.input3D[1].input3Dz, cd=main_con.scrunch, dv=-10, v=sdk_val)
            pm.setDrivenKeyframe(drn_plus.input3D[1].input3Dz, cd=main_con.scrunch, dv=10, v=sdk_val * -1)

            # spread on knuckle only
            if 'cup_{}'.format(drn_suf) in grps:
                pm.delete(pm.parentConstraint(ad_j, spread_aim_grp))
                aim_val = spread_aim.ry.get()
                pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.spread, dv=0, v=0)
                pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.spread, dv=-10, v=aim_val)
                pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.spread, dv=10, v=aim_val * -2)

            # extra multiplier
            drn_mult = common.create_name(side='', name=ad_j_name, fn='driven', _type='multiplyDivide', create=True)
            mult_at[ind].connect(drn_mult.i2x)
            mult_at[ind].connect(drn_mult.i2y)
            mult_at[ind].connect(drn_mult.i2z)
            drn_plus.output3D.connect(drn_mult.i1)
            drn_mult.output.connect(ad_con_dict[2].r)

        # clean up
        pm.delete(spread_aim_grp, spread_loc)

        # for cup on knuckle
        j_con_dict[3].rz.connect(cons[jnt][1].getParent(1).rz)

    # thumb
    if thumb:
        thumb_list = [thumb]
        thumb_list.extend(thumb.getChildren(ad=1, type='joint')[::-1])
        thumb_cons_list = shape_gen.create_chain(thumb_list[:-1], shape='sphere', groups=['offset', 'constraint', 'driven'],
                                                 con_scale=[con_scale] * 3)
        thumb_cons = [c[-1] for c in thumb_cons_list]
        main_ctrl_grp.addChild(thumb_cons[0].getAllParents()[-1])

        if mirror:
            temp_list = [c for c_list in thumb_cons_list for c in c_list if common.TYPE_LIST['offset'] in c.name()]
            for ind, con in enumerate(temp_list):
                prnt = None
                if ind < len(temp_list) - 1:
                    prnt = temp_list[ind + 1].getParent()
                    pm.parent(temp_list[ind + 1], w=1)

                con_prnt = con.getParent()
                if con_prnt:
                    pm.parent(con, w=1)
                new_rot = con.r.get()
                for i in range(3):
                    new_rot[i] += mir_rot[i]
                con.r.set(new_rot)
                con.s.set(mir_scale)

                if con_prnt:
                    pm.parent(con, con_prnt)

                if prnt:
                    pm.parent(temp_list[ind + 1], prnt)

        # constrain
        for ind, con in enumerate(thumb_cons):
            pm.parentConstraint(con, thumb_list[ind])
            con.s.connect(thumb_list[ind].s)
            # pm.scaleConstraint(con, thumb_list[ind])

        # for thumb spread
        point_loc = pm.spaceLocator()
        point_loc_grp = pm.group()
        pm.matchTransform(point_loc_grp, jnts[0])
        pm.matchTransform(point_loc, jnts[0].getChildren()[0])

        aim_loc = pm.spaceLocator()
        aim_loc_grp = pm.group()
        pm.aimConstraint(point_loc, aim_loc, aimVector=aim_v, upVector=up_v)
        pm.matchTransform(aim_loc_grp, thumb_list[0])

        # ssc
        [jnt.ssc.set(ssc) for jnt in thumb_list]

        # thumb cup
        pm.setDrivenKeyframe(thumb_cons[0].getParent().rz, cd=main_con.thumb_cup, dv=0, v=0)
        pm.setDrivenKeyframe(thumb_cons[0].getParent().rz, cd=main_con.thumb_cup, dv=10, v=-35)
        pm.setDrivenKeyframe(thumb_cons[0].getParent().rz, cd=main_con.thumb_cup, dv=-10, v=35)

        for ind, jnt in enumerate(thumb_list[1:-1]):
            thumb_name = common.replace_name(jnt.name(), 'joint', '')[:-1]
            drn_plus = common.create_name(side='', name=thumb_name, fn='driven', _type='plusMinusAverage', create=True)
            drn_plus.output3D.connect(thumb_cons[ind + 1].getParent().r)

            # fist
            val = 15 if ind == 0 else 90
            pm.setDrivenKeyframe(drn_plus.input3D[0].input3Dz, cd=main_con.thumb_fist, dv=0, v=0)
            pm.setDrivenKeyframe(drn_plus.input3D[0].input3Dz, cd=main_con.thumb_fist, dv=10, v=val * -1)
            pm.setDrivenKeyframe(drn_plus.input3D[0].input3Dz, cd=main_con.thumb_fist, dv=-10, v=val)

            # scrunch
            sdk_val = 0 if ind == 0 else 90
            pm.setDrivenKeyframe(drn_plus.input3D[1].input3Dz, cd=main_con.thumb_scrunch, dv=0, v=0)
            pm.setDrivenKeyframe(drn_plus.input3D[1].input3Dz, cd=main_con.thumb_scrunch, dv=-10, v=sdk_val)
            pm.setDrivenKeyframe(drn_plus.input3D[1].input3Dz, cd=main_con.thumb_scrunch, dv=10, v=sdk_val * -1)

            # spread on first and second
            if ind < 2:
                pm.matchTransform(point_loc_grp, jnt, pos=1)
                pm.matchTransform(aim_loc_grp, jnt)
                pm.parent(aim_loc_grp, jnt)
                aim_val = aim_loc.ry.get()
                if ind == 0:
                    aim_val *= .2
                else:
                    aim_val *= .8
                # pm.delete(pm.parentConstraint(ad_j, spread_aim_grp))
                # aim_val = spread_aim.ry.get()
                pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.thumb_spread, dv=0, v=0)
                pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.thumb_spread, dv=-10, v=aim_val)
                if ind == 0:
                    pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.thumb_spread, dv=10,
                                         v=aim_loc.ry.get() * -1)
                else:
                    pm.setDrivenKeyframe(drn_plus.input3D[2].input3Dy, cd=main_con.thumb_spread, dv=10, v=0)

        # clean up
        pm.delete(point_loc_grp, aim_loc_grp)

    return cons
