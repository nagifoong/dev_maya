import common
import pymel.all as pm
import rig_limbs
from rig_limbs import add_pointing_line

from ..utils import coloring, spaceswitch, mathNodes
from ..utilities.shapeCreator import main as shape_gen
from ..utils import channels


def hindLegIk_autoRig(jntList = [],side  ='' , prefix = '',conScale = 1,connectToMoCap = 0,worldCon = ''):
    '''
    Auto rig quadruped IK back leg.
    With pole vector pin, stretchy, auto aim, fk controller for hips
    :param jntList: list of five with specific order. eg: ['root','hip','gaskin','hock','fetlock']
    :param prefix: prefix for the system. eg: l_backLeg
    :return:
    '''
    '''creating groups for organizing'''
    #jntList = ['root','hip','knee','ankle','foot']
    nPrefix = "{}_{}".format(side,prefix)
    #prefix = "back_leg"
    color = coloring.colorDi[side]

    ## search no touch group to store nodes for calculation purpose
    if pm.ls('noTouch'):
        noTouchGrp = pm.ls('noTouch')[0]
    else:
        noTouchGrp = pm.group(name = "noTouch",em=1,w=1)

    ## search for groups to store controllers
    if pm.ls("{}_leg_GRP".format(side)):
        conTopGRP = pm.ls("{}_leg_GRP".format(side))[0]
    else:
        conTopGRP = pm.group(name = "{}_leg_GRP".format(side),em=1,w=1)

    utilGrp = pm.group(name="{}_util_GRP".format(nPrefix), em=1, parent=noTouchGrp)
    utilGrp.v.set(0)
    # ikConGrp = pm.group(name = "{}_main_CON_GRP".format(prefix),em=1,w=1)

    if pm.ls('spaceSwitch_GRP'):
        spaceSwitch_main = pm.ls('spaceSwitch_GRP')[0]
    else:
        spaceSwitch_main = pm.group(name="spaceSwitch_GRP", em=1, w=1)

    hip_off_con = pm.spaceLocator(name = "{}offset_CON_pxy".format(jntList[1].replace("JNT","")))
    hip_con = pm.group(name = hip_off_con.replace("_offset",""))
    hip_con_GRP =pm.group(name = "{}_GRP".format(hip_con))
    pm.delete(pm.parentConstraint(jntList[1],hip_con_GRP))
    hip_con_GRP.v.set(0,l=1)
    # pm.parentConstraint(hip_off_con, jntList[1], mo=1)

    '''create controls ikLegs'''
    nJntGrp = pm.group(name = "{}_IK_joints_GRP".format(nPrefix), em =1 , p = utilGrp)
    pm.parentConstraint(hip_off_con,nJntGrp)
    pm.scaleConstraint(worldCon, nJntGrp)

    nJntList = [jntList[0]]
    nJntList.extend(common.duplicate_joint_chain(nJntGrp, jntList[1:], "IKJ","JNT",  0))

    ikConGrp = pm.group(name = "{}_ik_main_GRP".format(nPrefix),p = conTopGRP,em=1)

    ikMain_con,ikMain_off_con = shape_gen.create_control("cube", name="{}_ik_CON".format(nPrefix),offsetCon=1)
    ikRoll_con,ikRoll_off_con = shape_gen.create_control("circle", name="{}_roll_CON".format(nPrefix),offsetCon=1)

    ikMain_con_grp = common.group_pivot(ikMain_con, mvp = True)
    ikRoll_con_grp = common.group_pivot(ikRoll_con, mvp = True)

    ikRoll_con_grp[0].rx.set(-90)
    ikRoll_con_grp[0].s.set([conScale, conScale, conScale])
    pm.makeIdentity(ikRoll_con_grp[0], apply=1, r=1,s=1)

    ikMain_con_grp[0].s.set([conScale, conScale, conScale])
    pm.makeIdentity(ikMain_con_grp[0], apply=1, s=1)

    ikMain_off_con.addChild(ikRoll_con_grp[0])


    pm.delete(pm.pointConstraint(nJntList[4],ikMain_con_grp[0]))
    pm.delete(pm.pointConstraint(nJntList[3],nJntList[4], ikRoll_con_grp[0]))
    pm.delete(pm.aimConstraint(nJntList[3],ikRoll_con_grp[0],aimVector = [0,0,-1]))

    pxyPos = pm.xform(jntList[4], q=1, ws=1, t=1)
    for grp in ikRoll_con_grp:
        pm.xform(grp, pivots=pxyPos, ws=1)

    pm.xform(ikRoll_con, pivots=pxyPos, ws=1)
    pm.xform(ikRoll_off_con, pivots=pxyPos, ws=1)
    ## adding attribute on ik main CON
    ikMain_con.addAttr("autoAim",at= "double",min=0,max=1,dv=1,k=1)

    spaceDict = {'pelvis': hip_con,
                 'root': jntList[0],
                 'space1': jntList[-1],
                 'world': ''}
    spaceswitch.create_space_switch_setup(space_dictionary=spaceDict, con_node=ikMain_con,
                                          parent_node_to=spaceSwitch_main, con_scale=1, setDefaultSpace='world')

    '''create ik system'''
    ikMain = pm.ikHandle(sj=nJntList[1],ee=nJntList[3],name = "{}_ikHandle".format(nPrefix))
    ikRoll = pm.ikHandle(sj=nJntList[3],ee=nJntList[4],name = "{}_roll_ikHandle".format(nPrefix))

    ikMain_grp = common.group_pivot(ikMain[0])
    ikRoll_grp = common.group_pivot(ikRoll[0])

    ikRoll_grp[-1].addChild(ikMain_grp[0])

    pm.parentConstraint(ikRoll_off_con,ikRoll_grp[0],mo=1)
    pm.scaleConstraint(worldCon, ikRoll_grp[0], mo=1)
    pv_distGrp, pv_distNode = common.create_distance_setup(setupName="{}_autoAim".format(nPrefix),
                                                               startPoint=hip_off_con, endPoint=ikMain_off_con,
                                                               constrainEnds=1)

    stretch_distNode =rig_limbs.make_chain_stretchy_trans(ikMain_con,nPrefix,nJntList[1:4],nJntList[3],parentTo = utilGrp,constraintLoc = 0)
    '''stretch_distGrp, stretch_distTrans = common.create_distance_setup(setupName="{}_stretch".format(nPrefix),
                                 startPoint=hip_con, endPoint=nJntList[3],
                                 constrainEnds=0)'''
    pm.scaleConstraint(worldCon,stretch_distNode.getParent().getParent())
    distLocs = [child for child in stretch_distNode.getParent().getChildren() if "_loc" in child.name()]
    pm.parentConstraint(hip_off_con, distLocs[0])
    pm.parentConstraint(ikRoll_off_con, distLocs[1], mo=1)

    #utilGrp.addChild(stretch_distGrp)
    utilGrp.addChild(pv_distGrp)
    utilGrp.addChild(ikRoll_grp[0])
    #common.stretchyIK_scale(jntList =nJntList[1:4] , prefix = prefix , distanceNode = stretch_distTrans.getChildren()[0], ctrl = ikMain_con)


    '''create pole vector controller'''
    pvMain_con,pvMain_off_con = shape_gen.create_control("sphere", name="{}_PV_CON".format(nPrefix),offsetCon=1)
    pvMain_grp = common.group_pivot(pvMain_con, mvp = True)

    pvMain_grp[0].s.set([conScale, conScale, conScale])
    pm.makeIdentity(pvMain_grp[0], apply=1, s=1)

    add_pointing_line(pvMain_con, pm.PyNode(nJntList[2]), name = "{}_PV_line".format(nPrefix))

    for con in [pvMain_con,pvMain_off_con]:
        channels.lock_channels(con, scales=[1, 1, 1], visibility=1)
        channels.display_channels(con, scales=[0, 0, 0], visibility=0)

    #pvMain_con.addAttr("lockMeDown",at= "double",min=0,max=1,dv=0,k=1)

    pvMain_grp[0].t.set(common.findPoleVector(jntList = nJntList[1:-1]))

    pm.poleVectorConstraint(pvMain_off_con,ikMain[0])

    ##Adding space switch attribute
    spaceDict = {'foot': ikMain_con,
                'pelvis':hip_con,
                'root': jntList[0],
                'space1':jntList[2],
                'world':''}

    spaceswitch.create_space_switch_setup(space_dictionary=spaceDict, con_node=pvMain_con,
                                          parent_node_to=spaceSwitch_main, con_scale=1, setDefaultSpace='foot')

    '''ik Roll auto aim'''
    totalLen = 0
    for jnt in nJntList[2:]:
        totalLen += abs(jnt.ty.get())

    aimMainGrp = pm.group( name = "{}_aimSys_GRP".format(nPrefix),em=1)
    aimLoc = pm.spaceLocator( name = "{}_aim_loc".format(nPrefix))
    offsetLoc = pm.spaceLocator( name = "{}_offsetAim_loc".format(nPrefix))

    aimMainGrp.addChild(aimLoc)
    aimMainGrp.addChild(offsetLoc)
    utilGrp.addChild(aimMainGrp)

    pm.delete(pm.parentConstraint(ikRoll_con,aimMainGrp))
    #pm.parentConstraint(ikMain_off_con,aimMainGrp,mo=1)
    pm.scaleConstraint(worldCon, aimMainGrp, mo=1)
    pm.delete(pm.orientConstraint(ikRoll_con,aimLoc))

    ikAsistJnts = ikAimSys(length=totalLen, start=hip_off_con, end=ikMain_off_con, prefix=nPrefix, parentTo=aimMainGrp)
    assistLoc = pm.spaceLocator(name = '{}_aimAssist_LOC'.format(side))
    pm.delete(pm.parentConstraint(ikAsistJnts[1], assistLoc))
    #pm.parentConstraint(hip_off_con,ikMain_off_con,assistLoc,mo=1)
    aimMainGrp.addChild(assistLoc)

    pm.aimConstraint(ikAsistJnts[1],offsetLoc, mo=0, aimVector = [0,0,-1] , upVector = [0,0,0], worldUpType = 'object' , worldUpObject =aimMainGrp)
    pm.aimConstraint(assistLoc,aimLoc, mo=1, aimVector = [0,0,-1] , upVector = [0,0,0], worldUpType = 'object' , worldUpObject =aimMainGrp)

    scaleFixNode = pm.createNode('multiplyDivide',name = "{}_aim_scaleFix_DIVD")
    scaleFixNode.operation.set(2)
    pv_distNode.distance.connect(scaleFixNode.input1X)
    worldCon.sy.connect(scaleFixNode.input2X)

    range_node = pm.shadingNode('setRange', au=1, name="{}_aim_RANGE".format(nPrefix))
    range_node.minX.set(0)
    range_node.maxX.set(1)
    range_node.oldMinX.set(pv_distNode.getChildren()[0].distance.get())
    range_node.oldMaxX.set(totalLen)
    scaleFixNode.outputX.connect(range_node.valueX)
    #pv_distNode.getChildren()[0].distance.connect(range_node.valueX)

    aim_node = pm.shadingNode('blendColors', au=1, name="{}_aim_BLEND".format(nPrefix))
    range_node.outValueX.connect(aim_node.blender)
    aimLoc.r.connect(aim_node.color2)
    offsetLoc.r.connect(aim_node.color1)

    switch_node = pm.shadingNode('multiplyDivide', au=1, name="{}_aim_switch_MULT".format(nPrefix))
    ikMain_con.autoAim.connect(switch_node.input1X)
    ikMain_con.autoAim.connect(switch_node.input1Y)
    ikMain_con.autoAim.connect(switch_node.input1Z)
    aim_node.output.connect(switch_node.input2)
    #switch_node.output.connect(ikRoll_con_grp[1].r)

    pinStretch_grps = rig_limbs.add_poleVector_lock(nPrefix,ikMain_con,pvMain_off_con,nJntList[1:4],nJntList[3],parentTo=utilGrp,constraintLoc = 0,attrTo = pvMain_con)
    #pinStretch_nodes = common.pinStretch(jntList=nJntList[1:4], pinCtrl= pvMain_con ,upParent=hip_con, loParent= ikRoll_con, parent_to=utilGrp)
    loPinLocs = [child for child in pinStretch_grps[1].getChildren() if "_loc" in child.name()]

    for loc in loPinLocs:
        if "distStart" in loc.name():
            pm.parentConstraint(pvMain_off_con,loc,mo=1)
        else:
            pm.parentConstraint(ikRoll_off_con, loc, mo=1)

    '''BALL / TOE IK proxy'''
    ballPxyOff = pm.group(name='{}_hindLeg_ball_IK_CON_offset_GRP'.format(side), em=1)
    ballPxyDRV = pm.group(name='{}_hindLeg_ball_IK_CON_DRV_GRP'.format(side),em=1, p=ballPxyOff)
    ballCon = shape_gen.create_control("circle", name='{}_hindLeg_ball_IK_CON'.format(side), offsetCon=1)
    #ballPxy = pm.group(name='{}_hindLeg_ball_IK_CON'.format(side), em=1, parent=ballPxyDRV)
    ballPxyDRV.addChild(ballCon[0])

    ballPxyOff.s.set([conScale, conScale, conScale])
    pm.makeIdentity(ballPxyOff, apply=1, r=1, s=1)

    pm.delete(pm.parentConstraint(nJntList[-1], ballPxyOff))
    pm.orientConstraint(ballCon[0], nJntList[-1], mo=1)

    '''FOOT FUNCTION'''
    # need to flip for LEFT or RIGHT
    flippingD = {'l': 1, 'r': -1, 'm': -1}

    if side == 'l':
        rollVal = {'min':-1,'max': -10}

    else:
        rollVal = {'min': 1, 'max': 10}
    if not pm.ls('tmpFeetPosition_GRP'):
        print "Missing tmpFeetPosition_GRP. Skipping foot roll creation"
        return

    ## [BankIn,BankOut,Heel,Toe]
    locs = [q for q in pm.ls('tmpFeetPosition_GRP')[0].getChildren(ad=1,type="transform") if side == q.name()[0] and 'loc' in q.name()]
    locs.sort()
    footRollGRPs =[]
    for loc in locs:
        grp = pm.group(name = loc.replace('tmp','').replace('loc','GRP'),em=1)
        pm.delete(pm.parentConstraint(loc,grp))
        if footRollGRPs:
            footRollGRPs[-1].addChild(grp)

        footRollGRPs.append(grp)

    ikMain_off_con.addChild(footRollGRPs[0])
    pm.parent(ikRoll_con_grp[0],ballPxyOff,footRollGRPs[-1])

    '''ROLL'''
    ikMain_con.addAttr('__footAttrs__', at='enum', en='___:',k=1)
    ikMain_con.addAttr('roll', attributeType='double', minValue=-1, maxValue=1,defaultValue=0,k=1)
    rollBack_RVN = mathNodes.create_remapValueNode('{}_ballRollBack'.format(nPrefix), inMin=0, inMax=-1, outMin=0,
                                                   outMax=-25)
    ikMain_con.roll.connect(rollBack_RVN.inputValue)
    rollBack_RVN.outValue.connect(footRollGRPs[2].rx)

    roll_backA_RVN = mathNodes.create_remapValueNode('{}_ballRollFront'.format(nPrefix), inMin=0, inMax=0.5, outMin=0,
                                                     outMax=-25)
    roll_backB_RVN = mathNodes.create_remapValueNode('{}_ballRollBack'.format(nPrefix), inMin=0.5, inMax=1, outMin=-25,
                                                     outMax=0)
    roll_CND = mathNodes.create_conditionNode('{}_roll'.format(nPrefix), operationVal=2)

    roll_CND.secondTerm.set(0.5)
    roll_backA_RVN.outValue.connect(roll_CND.colorIfFalseR)
    roll_backB_RVN.outValue.connect(roll_CND.colorIfTrueR)
    ikMain_con.roll.connect(roll_CND.firstTerm)
    ikMain_con.roll.connect(roll_backA_RVN.inputValue)
    ikMain_con.roll.connect(roll_backB_RVN.inputValue)

    rollTip_RVN = mathNodes.create_remapValueNode('{}_rollTip'.format(nPrefix), inMin=0.5, inMax=1, outMin=0, outMax=45)
    ikMain_con.roll.connect(rollTip_RVN.inputValue)
    rollTip_RVN.outValue.connect(footRollGRPs[3].rx)

    '''roll_amplitude'''
    ikMain_con.addAttr('roll_amplitude', attributeType='double', minValue=0, maxValue=1, defaultValue=0.5, k=1)
    nodeA = pm.createNode('multiplyDivide', n='{}_roll_amplitudeA_MDN'.format(nPrefix))
    # set val of input2X of MDN
    nodeA.i2x.set(2.5)
    nodeB = pm.createNode('multiplyDivide', n='{}_roll_amplitudeB_MDN'.format(nPrefix))

    rollAmplitude_RVN = mathNodes.create_remapValueNode('{}_roll_amplitude'.format(nPrefix), inMin=rollVal['min'], inMax=rollVal['max'], outMin=rollVal['min'],
                                                        outMax=rollVal['max'])

    rollWithAim_PLUS = pm.createNode('plusMinusAverage', name = "{}_rollWithAim_PLUS".format(nPrefix))

    # connections
    ikMain_con.roll_amplitude.connect(nodeA.i1x)
    nodeA.outputX.connect(rollAmplitude_RVN.inputValue)
    roll_CND.outColorR.connect(nodeB.i1x)
    switch_node.output.connect(rollWithAim_PLUS.input3D[0])
    rollAmplitude_RVN.outValue.connect(nodeB.i2x)
    nodeB.outputX.connect(rollWithAim_PLUS.input3D[1].input3Dx)
    rollWithAim_PLUS.output3D.connect(ikRoll_con_grp[1].r)

    '''TOE TAP'''
    ikMain_con.addAttr('toeTap', attributeType='double', minValue=-1, maxValue=1, defaultValue=0, k=1)
    toeTapRVN = mathNodes.create_remapValueNode('{}_toeTap'.format(nPrefix),
                                                inMin=-1, inMax=1, outMin=-35, outMax=35)
    ikMain_con.toeTap.connect(toeTapRVN.inputValue)
    toeTapRVN.outValue.connect(ballPxyDRV.rx)

    '''TOE PIVOT'''
    ikMain_con.addAttr('toePivot', attributeType='double', minValue=-1, maxValue=1, defaultValue=0, k=1)
    # toePivotRVN = mathNodes.create_remapValueNode('{}_toePivot'.format(prefix),
    #                                               inMin=defMinValue, inMax=defMaxValue, outMin=-25, outMax=25)
    toePivotRVN = mathNodes.create_remapValueNode('{}_toePivot'.format(nPrefix),
                                                  inMin=-1, inMax=1, outMin=flippingD[side] * -25,
                                                  outMax=flippingD[side] * 25)
    ikMain_con.toePivot.connect(toePivotRVN.inputValue)
    toePivotRVN.outValue.connect(footRollGRPs[-1].ry)

    '''HEEL PIVOT'''
    ikMain_con.addAttr('heelPivot', attributeType='double', minValue=-1, maxValue=1, defaultValue=0, k=1)

    heelPivotRVN = mathNodes.create_remapValueNode('{}_heelPivot'.format(prefix),
                                                   inMin=-1, inMax=1,
                                                   outMin=flippingD[side] * -25, outMax=flippingD[side] * 25)
    ikMain_con.heelPivot.connect(heelPivotRVN.inputValue)
    heelPivotRVN.outValue.connect(footRollGRPs[-2].ry)

    '''BANK IN AND OUT'''
    ikMain_con.addAttr('bank', attributeType='double', minValue=-1, maxValue=1, defaultValue=0, k=1)
    bankInRMV = mathNodes.create_remapValueNode('{}_bankIn'.format(prefix),
                                                inMin=0, inMax=-1,
                                                outMin=0, outMax=flippingD[side] * 45)
    bankOutRMV = mathNodes.create_remapValueNode('{}_bankOut'.format(prefix),
                                                 inMax=1, outMax=flippingD[side] * -45)
    ikMain_con.bank.connect(bankInRMV.inputValue)
    ikMain_con.bank.connect(bankOutRMV.inputValue)
    bankInRMV.outValue.connect(footRollGRPs[0].rz)
    bankOutRMV.outValue.connect(footRollGRPs[1].rz)


    '''Organize grouping & clean up'''
    # constraint to last foot roll grp
    pm.parentConstraint(hip_off_con, footRollGRPs[-1], assistLoc, mo=1)
    pm.parentConstraint(footRollGRPs[-1], aimMainGrp, mo=1)

    ikConGrp.addChild(ikMain_con_grp[0])
    ikConGrp.addChild(pvMain_grp[0])

    common.setTopNodeMessages(ikConGrp, nJntGrp, 'IK', ikConGrp)
    ikConGrp.addAttr('ikPoleVector', attributeType='message')
    pvMain_con.message.connect(ikConGrp.ikPoleVector)
    ikConGrp.addAttr('ik_con', attributeType='message')
    ikMain_con.message.connect(ikConGrp.ik_con)

    # not edited
    # if connectToMoCap:
    #     common.mocap_create_connection(jntList[0], ikMain_con_grp, 'direct')
    #     common.mocap_create_connection(jntList[1], ikMain_con_grp, 'direct')
    for con in [ikMain_con,ikRoll_con,pvMain_con,ballCon[0]]:
        coloring.setOverrideColor(con, color)

    return {'topIK':ikConGrp,
            'hipCons':[hip_con_GRP,hip_con,hip_off_con],
            'ikConsList': [ikMain_con,ikRoll_con,pvMain_con,ballCon[0]]}

def ikAimSys(length = 1.0,start = '', end = '',prefix = '', parentTo = '' ):
    '''
    quadruped hind leg aim system
    :param length: length of straighten leg
    :param start: start joint
    :param end: end joint
    :param prefix: name of system
    :param parentTo: parent to
    :return:
    '''
    pm.select(cl=1)
    # length = 10
    # prefix = 'l_leg_pxy'
    diff = length / 2.0
    current = 0
    jntList = []
    prefix = prefix+"_aimAssist"
    for q in range(1, 4):

        jnt = pm.joint(name="{}_{}_JNT".format(prefix, q), p=(0,current, 0))
        if q == 2:
            jnt.rx.set(45)
            pm.joint(jnt, e=1, spa=1)
            jnt.rx.set(0)
        current += diff
        jntList.append(jnt)
    ikHdl = pm.ikHandle(sj=jntList[0], ee=jntList[-1], name='{}_ikHandle'.format(prefix))#,sol = 'ikSCsolver')
    pm.rename(ikHdl[1],"{}_endEffector".format(prefix))
    ikHdlGrp = pm.group(name="{}_GRP".format(ikHdl[0]), em=1, w=1)
    pm.delete(pm.parentConstraint(ikHdl[0], ikHdlGrp))
    ikHdlGrp.addChild(ikHdl[0])

    pm.pointConstraint(start,jntList[0])
    pm.delete(pm.pointConstraint(end, ikHdlGrp))

    if parentTo:
        pm.parent(jntList[0],ikHdlGrp,parentTo)

    return jntList

# def hindLegFk_autoRig(jntList = [],side  ='' , prefix = '',con_scale = 1,connectToMoCap = 0,hipCon = ""):
#     '''
#
#     :param jntList: [toe]
#     :param side:
#     :param con_scale:
#     :return:
#     '''
#     topFK, fkConList = rig_limbs.create_fk_setup(side, prefix, jntList[1:],
#                                                  parent_to=parent, attachTo=attach_to_node,
#                                                  con_scale=con_scale, connectChain=0,
#                                                  fk_con_type='', connectMocap=connectToMoCap, hipCon=hipCon)
#
#     return

def hindLeg_autoRig(jntList = [],side  ='' , prefix = '',conScale = 1,connectToMoCap = 0,parent = '',attach_to = ''):
    '''
    auto rig quadruped hind leg main script
    :param jntList: list of five with specific order. eg: ['root','hip','gaskin','hock','fetlock']
    :param side: "l"/"r"
    :param prefix: name of system
    :param conScale: scale value for controllers
    :param connectToMoCap: obsolete for now
    :param parent: parent group for fk system
    :param attach_to:  constraint to
    :return: topIK, topFK nodes
    '''
    color = coloring.colorDi[side]
    nConScale = conScale / 2.0
    if pm.ls('noTouch'):
        noTouchGrp = pm.ls('noTouch')[0]
    else:
        noTouchGrp = pm.group(name = "noTouch",em=1,w=1)

    if pm.ls('spaceSwitch_GRP'):
        worldCon = pm.PyNode('world_CON')
        spaceSwitch_main = pm.ls('spaceSwitch_GRP')[0]
    else:
        worldCon = pm.group(name = 'scaleParent',em=1 , p = noTouchGrp)
        spaceSwitch_main = pm.group(name="spaceSwitch_GRP", em=1, w=1)

    if pm.ls("{}_leg_GRP".format(side)):
        conTopGRP = pm.ls("{}_leg_GRP".format(side))[0]
    else:
        conTopGRP = pm.group(name = "{}_leg_GRP".format(side),em=1,w=1)

    ikDict = hindLegIk_autoRig(jntList=jntList, side=side, prefix=prefix,
                                          conScale=nConScale,worldCon=worldCon)


    topFK, fkConList = rig_limbs.create_fk_setup(side, prefix, jntList[1:],
                                                 parentTo=conTopGRP, attachTo=attach_to,
                                                 conScale=conScale, connectChain=0,
                                                 fk_con_type='', connectMocap=connectToMoCap, hipCon=ikDict['hipCons'][-1])

    '''create controls for hips'''
    if pm.ls('{}_hip_GRP'.format(side)):
        hipMainGRP = pm.ls('{}_hip_GRP'.format(side))[0]
    else:
        hipMainGRP = pm.group(name = '{}_hip_GRP'.format(side),em=1,w=1)

    hipRot_con,hipRot_off_con = shape_gen.create_control("circle", name=jntList[1].replace('JNT','rot_CON'),offsetCon=1)
    hip_con,hip_off_con = shape_gen.create_control("arrowRot4WaysY", name=jntList[1].replace('JNT','CON'),offsetCon=1)

    hipRot_grp = common.group_pivot(hipRot_con, mvp = True)
    hip_grp = common.group_pivot(hip_con, mvp = True)

    hipRot_grp[0].rz.set(-90)
    hipRot_grp[0].s.set([nConScale,nConScale,nConScale])
    hip_grp[0].rz.set(-90)
    hip_grp[0].s.set([nConScale, nConScale, nConScale])

    pm.makeIdentity(hipRot_grp[0], apply=1, r=1,s=1)
    pm.makeIdentity(hip_grp[0], apply=1, r=1,s=1)

    pm.delete(pm.pointConstraint(jntList[1],hipRot_grp[0], mo=0))
    pm.delete(pm.pointConstraint(jntList[1],hip_grp[0], mo=0))

    ## change pivot to root
    rootLoc = pm.xform(jntList[0],q=1,ws=1,t=1)
    for grp in hipRot_grp:
        pm.xform(grp,pivots = rootLoc, ws=1)

    pm.xform(hipRot_con,pivots = rootLoc, ws=1)
    pm.xform(hipRot_off_con, pivots=rootLoc, ws=1)
    hipRot_off_con.addChild(hip_grp[0])

    pm.parentConstraint(hip_off_con,ikDict['hipCons'][1], mo = 1)
    # hipMainGRP.addChild(hipRot_grp[0])
    pm.parent(hipRot_grp[0],ikDict['hipCons'][0],hipMainGRP)

    ##Adding space switch attribute
    spaceDict = {'root': jntList[0],
                 'space1': jntList[1],
                 'world': ''}

    spaceswitch.create_space_switch_setup(space_dictionary=spaceDict, con_node=hipRot_con, parent_node_to=spaceSwitch_main,
                                          con_scale=1, setDefaultSpace='root')

    ## lock channels are not intended to use
    for con in [hipRot_con,hipRot_off_con]:
        channels.lock_channels(con, translates=[1, 1, 1], scales=[1, 1, 1], visibility=1)
        channels.display_channels(con, translates=[0, 0, 0], scales=[0, 0, 0], visibility=0)

    for con in [hip_con,hip_off_con]:
        channels.lock_channels(con, rotate=[1, 1, 1], scales=[1, 1, 1], visibility=1)
        channels.display_channels(con, rotate=[0, 0, 0], scales=[0, 0, 0], visibility=0)

    for con in [hip_con,hipRot_con]:
        coloring.setOverrideColor(con, color)

    return ikDict['topIK'],topFK