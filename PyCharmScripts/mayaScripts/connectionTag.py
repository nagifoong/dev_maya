from bfx_rig_vfx_internal.rigging.rigHQ import connectionCreator

def findConnectionType(obj,filterPath ='custom_rig_GRP',deleteConnection = 1):
    '''
    find input connection type of obj, exclude anything which is not under filterPath.
    :param obj: object
    :param filterPath: skip connection that is not under "filterPath"
    :param deleteConnection: delete connection
    :return:
    '''
    ## find connection type **input only
    if not obj.inputs():
        return None
    inputs = []
    attrs = []
    prev = ''
    restDict = {}

    ## seperate source and destination
    for inp in obj.inputs(c=1, p=1):
        if inp[1].nodeName() in [q.nodeName() for q in inputs] and "Constraint" in inp[1].node().type():
            continue
        inputs.append(inp[1])
        attrs.append(inp[0])

    for ind ,inp in enumerate(inputs):
        conn = inp.node()
        if 'Constraint' in conn.type() and prev != conn.name():
            ##work for one parent
            parents = conn.getTargetList()
            for prnt in parents:
                if filterPath in prnt.fullPath() and filterPath:
                    break
                if conn.type() not in restDict:
                    restDict[conn.type()] = [prnt.name(), obj.name()]
                else:
                    restDict.update({conn.type():[prnt.name(), obj.name()]})

                if deleteConnection:
                    pm.delete(inp.node())
            prev = conn.name()

        elif 'Constraint' not in conn.type():
            ## calculation nodes
            if inp.node().type() != "transform" and attrs[ind].attrName() != "is" :
                if 'direct' not in restDict:
                    restDict['direct'] = [inp.name(), attrs[ind].name()]
                else:
                    restDict.update({'direct':[inp.name(), attrs[ind].name()]})

            ## transform nodes
            elif filterPath not in inp.node().fullPath():
                if 'direct' not in restDict:
                    restDict['direct'] = [inp.name(), attrs[ind].name()]
                else:
                    restDict.update({'direct':[inp.name(), attrs[ind].name()]})
            if deleteConnection:
                inp.disconnect(attrs[ind])
    return restDict

reload(connectionCreator)
TAG = connectionCreator.Connector()

cusGRPs = ['custom_cons_GRP', 'custom_joints_GRP']
# pm.selected()[0].getTargetList()
# TAG.PARENTING_PAIRS['extra_joints_GRP'] = ['custom_joints_GRP']
# TAG.PARENTING_PAIRS['controlRig_GRP'] = ['custom_cons_GRP']
# TAG.CONSTRAINTS_SCALE['world_CON'] = [['custom_joints_GRP', 1]]
# pm.delete(pm.PyNode('custom_joints_GRP').s.inputs(type = "scaleConstraint"))

# define variable before parent them in to newGRP
for grp in cusGRPs:
    if not pm.ls(grp):
        continue
    pyGrp= pm.PyNode(grp)

    TAG.PARENTING_PAIRS[pyGrp.getParent().name()] = [grp]

    connDict = findConnectionType(pyGrp)
    if not connDict:
        continue
    for key,value in connDict.items():
        if key == "parentConstraint":
            TAG.CONSTRAINTS_PARENT[value[0]] = [[value[1], 1]]
        if key == "orientConstraint":
            TAG.CONSTRAINTS_OREINT[value[0]] = [[value[1], 1]]
        if key == "scaleConstraint":
            TAG.CONSTRAINTS_SCALE[value[0]] = [[value[1], 1]]
        if key == "direct":
            TAG.CONNECT_ATTR[value[0]] = [value[1]]


if not pm.ls("custom_rig_GRP"):
    cusRigGRP = pm.group(name = "custom_rig_GRP",em=1)
else:
    cusRigGRP = pm.PyNode("custom_rig_GRP")
pm.parent(cusGRPs,cusRigGRP)

for grp in cusGRPs:
    if not pm.ls(grp):
        continue
    for child in pm.PyNode(grp).getChildren(ad=1):
        if 'Constraint' in child.type():
            continue
        connDict = findConnectionType(child)
        if connDict:
            for key, value in connDict.items():
                if key == "parentConstraint":
                    TAG.CONSTRAINTS_PARENT[value[0]] = [[value[1], 1]]
                if key == "orientConstraint":
                    TAG.CONSTRAINTS_OREINT[value[0]] = [[value[1], 1]]
                if key == "scaleConstraint":
                    TAG.CONSTRAINTS_SCALE[value[0]] = [[value[1], 1]]
                if key == "direct":
                    TAG.CONNECT_ATTR[value[0]] = [value[1]]

        if child.type() == 'joint' and pm.ls("DEF_{}".format(child.name())):
            defJnt = pm.PyNode("DEF_{}".format(child.name()))
            for ty in 'trs':
                child.attr(ty).disconnect(defJnt.attr(ty))
TAG.taggedNode_create(parentTo='custom_rig_GRP')
