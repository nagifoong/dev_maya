import pymel.all as pm
import maya.cmds as cmds
import maya.mel as mel

from ...utils import skinning

reload(skinning)

ROUND_DECIMAL = 4


def get_point_position(node):
    """
    get component world position
    :param node:
    :return:
    """
    output = []

    # find cv
    component = cmds.ls("{}.cv[*]".format(node), fl=1)
    if not component:
        # find vertices if cv does not exist
        component = cmds.ls("{}.vtx[*]".format(node), fl=1)

    # find world position of the component
    for comp in component:
        output.append([round(q, ROUND_DECIMAL) for q in cmds.xform(comp, q=1, ws=1, t=1)])

    return output


def get_wire_weight(sel):
    """
    get wire weight by transforming curve cv to 1 and list down the transformed vertex value
    :param sel: [curve, mesh]
    :return: weight for the wire
    """
    crv = sel[0]
    mesh = sel[1]
    delta = []

    # disable rotation on wire deformer
    wire_rotation = {}
    for wire in pm.ls(type='wire'):
        wire_rotation[wire] = wire.rotation.get()
        wire.rotation.set(0)

    # get original world position of curve and mesh
    crv_orig = get_point_position(crv)
    mesh_orig = get_point_position(mesh)

    # list all cv in curve and its amount
    cvs = cmds.ls('{}.cv[*]'.format(crv), fl=1)
    cv_count = len(cvs)

    for ind, cv in enumerate(cvs):
        # reset position
        [cmds.xform('{}.cv[{}]'.format(crv, c), ws=1, t=crv_orig[c]) for c in range(cv_count)]

        # transform cv to +y 1
        cmds.xform(cv, ws=1, t=[0, 1, 0])

        # get transformed vertices position
        current = get_point_position(mesh)

        # calculate delta
        delta.append([[round(current[i] - orig[i], ROUND_DECIMAL) for i in range(3)]
                      for orig, current in zip(mesh_orig, current)])

    # reset when done
    [cmds.xform('{}.cv[{}]'.format(crv, c), ws=1, t=crv_orig[c]) for c in range(cv_count)]

    # restore wire rotation
    for wire in wire_rotation:
        wire.rotation.set(wire_rotation[wire])

    return delta


def convert_wire_to_skin(sel):
    """
    get wire weight and convert it as skin weight
    :param sel: [curve, mesh]
    :return:
    """
    crv = sel[0]
    mesh = sel[1]

    joints = []
    delta = get_wire_weight(sel)

    cvs = cmds.ls('{}.cv[*]'.format(crv), fl=1)
    for ind, cv in enumerate(cvs):
        # create joint
        jnt = pm.createNode('joint', name='{}_{}_jnt'.format(crv, str(ind).zfill(len(str(len(cvs) + 1)))))
        jnt.t.set(cmds.xform(cv, q=1, ws=1, t=1))
        joints.append(jnt)

    # find skin cluster
    scl = skinning.get_skin_cluster(mesh)
    orig_weight = []
    if not scl:
        # add hold joint if skin cluster does not exist
        joints.append(pm.createNode('joint', name='{}_hold_jnt'.format(crv)))
        scl = skinning.create_scl(joints, mesh)
    else:
        # get original skin weight and add new joint to skinCluster
        orig_weight = [w for w in scl.getWeights(mesh)]
        scl.addInfluence(joints)
        joints = scl.influenceObjects()

    # compile skin weight data
    new_weights = []
    for pnt in range(mesh.numVertices()):
        weight = [jnt[pnt][1] for jnt in delta]

        # make sure sum of the weight does not exceed 1.0
        if sum(weight) > 1.0:
            weight = [w/sum(weight) for w in weight]

        # if original weight exists, make sure divide it by the weight from the new joints
        if orig_weight:
            temp = [w * (1-sum(weight)) for w in orig_weight[pnt]]
            temp.extend(weight)
            weight = temp
        else:
            # skin weight for hold joint
            weight.append(1-sum(weight))

        new_weights.extend(weight)

    # set weights
    scl.setWeights(mesh.getShapes(ni=1)[0], range(len(joints)), new_weights, False)
    return scl
