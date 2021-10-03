
import pymel.all as pm

from ...rigHQ import connectionCreator

reload(connectionCreator)

TOP_GRP_NAME = 'customRig_GRP'
GRP_NAMES = ['customRig_joints_GRP',
             'customRig_cons_GRP',
             'customRig_geo_GRP',
             'customRig_noTouch_GRP']
dagNodes = pm.ls(dag=1)
def init_nodes(reorder = False):
    """
    create top node groups (top + grps)
    check if they exists or not first.
    """
    print('setting up top nodes for customRig file')

    # {'rig': '', 'joints': '', 'cons': ''}
    grpsDict = {}

    if not pm.ls(TOP_GRP_NAME):
        topGrp = pm.group(em=1, name=TOP_GRP_NAME)
    else:
        topGrp = pm.PyNode(TOP_GRP_NAME)

    grpsDict['rig'] = topGrp

    for grp in GRP_NAMES:
        key = grp.split("_")[1]
        if not pm.ls(grp):
            grp = pm.group(em=1, name=grp)
        else:
            grp = pm.PyNode(grp)
        grpsDict[key] = grp
        if reorder:
            if grp.getParent():
                grpsDict['{}OriParent'.format(grp)] = grp.getParent()
            grp.setParent(topGrp)

    return grpsDict

def check_customRig():

    print 'checking nodes for customRig file'

    resDict = init_nodes()
    # check that all joint rotation are [0,0,0]
    # check_joint_rotations()

    # check joint names
    check_names(type='joints')

    # check con names (_CON + OFFSET + NUL)
    check_names(type = 'cons')

    # writing joint apose attributes attributes
    from ...utilities.skeleton_template import skeleton_data
    reload(skeleton_data)
    skeleton_data.write_default(resDict['joints'])


    #-- need to create TAG locator here?
    analyzeScene()

    # add metas to cons group.
    pm.select(resDict['rig'])


# def check_joint_rotations():
#
#     print 'checking all joint rotations'

def check_names(type =''):

    # print 'check the names for cons and joints'
    if type == 'joints':
        print "# Check joints in scene."
        for jnt in pm.ls(type = 'joint'):
            if "JNT" not in jnt.name() and GRP_NAMES[0] in jnt.fullPath():
                if jnt.name()[-1] != "J":
                    continue
                print "Renaming {} to {}_JNT".format(jnt,jnt)
                jnt.rename("{}_JNT".format(jnt))
        return
    if type == 'cons':
        print "# Check CON in scene."
        for conShp in pm.ls('*CON',type = 'nurbsCurve'):
            if "offset" not in conShp.name():
                con = conShp.getParent()
                offName = "{}_OFFSET".format(con)
                nulName = "{}_NUL".format(con)

                ## create groups for con
                if not pm.ls(nulName):
                    nulGRP = pm.group(name = nulName, em =1 , p = con.getParent())
                    pm.delete(pm.parentConstraint(con, nulGRP))
                    pm.parent(con,nulGRP)

                if not pm.ls(offName):
                    nulGRP = pm.group(name=offName, em=1, p=con.getParent())
                    pm.delete(pm.parentConstraint(con, offName))
                    pm.parent(con, offName)
        return

def analyzeScene():

    TAG = connectionCreator.Connector()

    # TAG.CONSTRAINTS_PARENT['l_elbow_JNT'] = [['l_forearmPanel_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['r_elbow_JNT'] = [['r_forearmPanel_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['l_upArm_JNT'] = [['l_uprarmPanel_CON_NUL', 1], ['l_shoulderPanel_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['r_upArm_JNT'] = [['r_uprarmPanel_CON_NUL', 1], ['r_shoulderPanel_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['m_root_JNT'] = [['m_belt_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['m_spine1_JNT'] = [['r_torsoBox01_CON_NUL', 1], ['l_torsoBox01_CON_NUL', 1],
    #                                           ['r_torsoBox02_CON_NUL', 1], ['l_torsoBox02_CON_NUL', 1],
    #                                           ['r_torsoBox03_CON_NUL', 1], ['l_torsoBox03_CON_NUL', 1],
    #                                           ['r_torsoBox04_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['m_spine2_JNT'] = [['m_torsoCylinder_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['r_knee_JNT'] = [['r_kneePad_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['l_knee_JNT'] = [['l_kneePad_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['m_head_JNT'] = [['m_helmet_CON_NUL', 1]]
    # TAG.CONSTRAINTS_PARENT['r_upLeg_JNT'] = [['r_pistol_CON_NUL', 1]]
    #
    # TAG.CONSTRAINTS_SCALE['world_CON'] = [['custom_joints_GRP', 1]]



    # create tag node with defined dictionaries
    # TAG.taggedNode_create(parent_to='custom_rig_GRP')

    # read the locator atributes
    # TAG.taggedNode_read()
    #
    # # read data
    # TAG.read()
    #
    # # create connections on rig
    # TAG.run_tag_connections()

    # cusGRPs = GRP_NAMES
    resDict = init_nodes(reorder= True)

    ''' @NAGI
    # cusGRPS = [resDict['joints'],resDict['cons']]
    ### >>> what is the point of this  making a list from a dictionary we created in init_nodes(). 
    ### >>> we have global variable for it already. Just use that instead GRP_NAMES
    '''
    ## get pynode of the group
    cusGRPS =[]
    for key in resDict:
        if key == 'rig':
            continue
        else:
            cusGRPS.append(resDict[key])
    cusGRPS = [resDict['joints'],resDict['cons']]
    # pm.selected()[0].getTargetList()
    # TAG.PARENTING_PAIRS['extra_joints_GRP'] = ['custom_joints_GRP']
    # TAG.PARENTING_PAIRS['controlRig_GRP'] = ['custom_cons_GRP']
    # TAG.CONSTRAINTS_SCALE['world_CON'] = [['custom_joints_GRP', 1]]
    # pm.delete(pm.PyNode('custom_joints_GRP').s.inputs(type = "scaleConstraint"))

    # define cons_GRP and jnt_GRP variable before parent them in to newGRP
    TAG.PARENTING_PAIRS['extra_joints_GRP'] = [resDict['joints'].name()]

    if resDict['{}OriParent'.format(resDict['cons'])]:
        TAG.PARENTING_PAIRS[resDict['{}OriParent'.format(resDict['cons'])].name()] = [resDict['cons'].name()]  # @NAGI Fix this hard coded line

    else:
        TAG.PARENTING_PAIRS[resDict['cons'].getParent().name()] = [resDict['cons'].name()]  # @NAGI Fix this hard coded line

    for bs in pm.ls(type = 'blendShape'):
        outGeoms = bs.getGeometry()
        for ind,geom in enumerate(outGeoms):
            geom = pm.PyNode(geom)
            if TOP_GRP_NAME not in geom.fullPath():
                fullAt= "{}.outputGeometry[{}]".format(bs,ind)
                if TAG.CONNECT_ATTR.get(fullAt):
                    TAG.CONNECT_ATTR[fullAt].append("{}.inMesh".format(geom))
                    continue
                TAG.CONNECT_ATTR[fullAt] = ["{}.inMesh".format(geom)]
                pm.PyNode(fullAt).disconnect(geom.inMesh)

        wInputs = bs.weight.inputs()
        enInput = bs.envelope.inputs(p=1)
        if enInput:
            if TAG.CONNECT_ATTR.get(enInput[0]):
                TAG.CONNECT_ATTR[enInput[0]].append("{}.envelope".format(bs))
                continue
            TAG.CONNECT_ATTR[enInput[0]] = ["{}.envelope".format(bs)]

        if wInputs:
            bsLoc = pm.spaceLocator(name = '{}_connLOC'.format(bs))
            pm.parent(bsLoc,GRP_NAMES[-1])
            for inp in wInputs:
                if "animCurve" in inp.type():
                    prevConn = inp.input.inputs(p=1,c=1,sourceFirst=1)[0]
                    atName = prevConn[0].replace('.','__')
                    bsLoc.addAttr(atName,at= 'double',k=1)
                    prevConn[0].connect(bsLoc.attr(atName))
                    bsLoc.attr(atName).connect(prevConn[1],force=1)

    for grp in cusGRPS:
        # if not pm.ls(grp):
        #     continue
        # pyGrp = pm.PyNode(grp)
        # # TAG.PARENTING_PAIRS[pyGrp.getParent().name()] = [grp]

        connDict = findConnectionType(grp)
        # print connDict
        if not connDict:
            continue
        for key, values in connDict.items():
            for value in values:
                if key == "parentConstraint":
                    TAG.CONSTRAINTS_PARENT[value[0]] = [[value[1], 1]]
                if key == "orientConstraint":
                    TAG.CONSTRAINTS_OREINT[value[0]] = [[value[1], 1]]
                if key == "scaleConstraint":
                    TAG.CONSTRAINTS_SCALE[value[0]] = [[value[1], 1]]
                if key == "direct":
                    if TAG.CONNECT_ATTR.get(value[0]):
                        TAG.CONNECT_ATTR[value[0]].append(value[1])
                        continue
                    TAG.CONNECT_ATTR[value[0]] = [value[1]]
        for ty in 'trs':
            for ax in 'xyz':
                grp.attr(ty+ax).set(l=0)

    # if not pm.ls("custom_rig_GRP"):
    #     cusRigGRP = pm.group(name="custom_rig_GRP", em=1)
    # else:
    #     cusRigGRP = pm.PyNode("custom_rig_GRP")
    # pm.parent(cusGRPs, cusRigGRP)

    for grp in cusGRPS:
        for child in pm.PyNode(grp).getChildren(ad=1,ni=1):
            if not child:
                continue
            if 'Constraint' in child.type():
                continue
            connDict = findConnectionType(child)
            if connDict:
                for key, values in connDict.items():
                    for value in values:
                        if key == "parentConstraint":
                            TAG.CONSTRAINTS_PARENT[value[0]] = [[value[1], 1]]
                        if key == "orientConstraint":
                            TAG.CONSTRAINTS_OREINT[value[0]] = [[value[1], 1]]
                        if key == "scaleConstraint":
                            TAG.CONSTRAINTS_SCALE[value[0]] = [[value[1], 1]]
                        if key == "direct":
                            if TAG.CONNECT_ATTR.get(value[0]):
                                TAG.CONNECT_ATTR[value[0]].append(value[1])
                                continue
                            TAG.CONNECT_ATTR[value[0]] = [value[1]]

            # if child.type() == 'joint' and pm.ls("DEF_{}".format(child.name())):
            #     defJnt = pm.PyNode("DEF_{}".format(child.name()))
            #     for ty in 'trs':
            #         child.attr(ty).disconnect(defJnt.attr(ty))
            #         for ax in 'xyz':
            #             child.attr(ty+ax).set(l=0)

    TAG.taggedNode_create(parentTo=resDict['cons'])

def findConnectionType(obj, filterPath=TOP_GRP_NAME, deleteConnection=1):
    '''
    find input connection type of obj, exclude anything which is not under filterPath.
    :param obj: object
    :param filterPath: skip connection that is not under "filterPath"
    :param deleteConnection: delete connection
    :return:
    '''
    ## find connection type **input only
    if not obj.listConnections():
        return None
    inputs = []
    attrs = []
    prev = ''
    restDict = {}
    constToDelete = []
    ## seperate source and destination
    for inp in obj.listConnections(c=1, p=1,sourceFirst=1):
        if (inp[1].nodeName() in [q.nodeName() for q in inputs] and "Constraint" in inp[1].node().type()) or inp[0].attrName() in ['id','mwc','vt'] or \
                        inp[1].nodeName() == "MayaNodeEditorSavedTabsInfo" and (inp[0].nodeType() == 'blendShape' and inp[1].nodeType() == 'blendShape'):
            continue
        inputs.append(inp[1])
        attrs.append(inp[0])


    for ind, inp in enumerate(inputs):
        conn = inp.node()
        print 'asdsadas',attrs[ind], conn
        if attrs[ind].node() == conn:
            continue

        if 'Constraint' in conn.type():

            if prev != conn.name():
                ##work for one parent
                parents = conn.getTargetList()
                for prnt in parents:
                    if (filterPath in prnt.fullPath() and filterPath in inp.node().fullPath()) and filterPath :
                        break
                    if conn.type() not in restDict:
                        restDict[conn.type()] = [(prnt.name(), conn.getParent().name())]
                    else:
                        restDict[conn.type()].append((prnt.name(),  conn.getParent().name()))

                    if deleteConnection:
                        for ty in 'trs':
                            for ax in 'xyz':
                                conn.getParent().attr(ty+ax).set(l=0)
                        constToDelete.append(inp.node())
                prev = conn.name()

        elif 'Constraint' not in conn.type() and 'Constraint' not in attrs[ind].nodeType():

            ## calculation nodes
            if inp.node().type() not in  ["transform",'joint'] and inp.attrName() != "is":
                if 'direct' not in restDict:
                    restDict['direct'] = [(attrs[ind].name(),inp.name())]
                else:
                    restDict['direct'].append((attrs[ind].name(),inp.name()))

            ## transform nodes
            elif filterPath not in inp.node().fullPath():
                # Skipping def joints
                if "DEF" in inp.nodeName() and  (attrs[ind].nodeName() == inp.nodeName().replace('DEF_','')):
                    attrs[ind].disconnect(inp)
                    continue
                if 'direct' not in restDict:
                    restDict['direct'] = [(attrs[ind].name(), inp.name())]
                else:
                    restDict['direct'].append((attrs[ind].name(), inp.name()))

            if deleteConnection:
                # print "Brake {} ,{}".format(attrs[ind],inp)
                inp.set(l=0)
                attrs[ind].set(l=0)
                attrs[ind].disconnect(inp)
                # inp.disconnect(attrs[ind])

    if deleteConnection:
        pm.delete(constToDelete)

    return restDict