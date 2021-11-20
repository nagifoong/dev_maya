import maya.OpenMaya as om
import pymel.all as pm
import re

from ..tools import controllerShape as shape_gen
import vertsFunc
from ..data import name_data, color_data

reload(name_data)
reload(color_data)
reload(shape_gen)
reload(vertsFunc)

atName = {'t': 'trans', 'r': 'rot', 's': 'scale'}

TYPE_LIST = name_data.TYPE_LIST
SIDE_LIST = name_data.SIDE_LIST
SIDE_COLOR = color_data.SIDE_COLOR
COLOR_DICT = color_data.COLOR_DICT


def replace_name(obj, old, new, case_sensitive=True):
    """
    replace name with type list. New argument accept ":" as multiple input
    """
    old = TYPE_LIST[old] if old in TYPE_LIST.keys() else old
    if ':' not in new:
        new = TYPE_LIST[new] if new in TYPE_LIST.keys() else new
    else:
        # use : to separate new names
        replaced = []
        for n in new.split(':'):
            replaced.append(TYPE_LIST[n] if n in TYPE_LIST.keys() else n)
        new = '_'.join(replaced)

    # find word with case insensitive
    if not case_sensitive:
        se = re.search(old, obj, re.IGNORECASE)
        if se:
            old = se.group(0)

    new_name = obj.replace(old, new)

    if isinstance(obj, pm.PyNode):
        obj.rename(new_name)

    return new_name


def create_name(side='middle', name='default', fn='', _type='group', create=False, find=False):
    str_list = []
    type_name = ''
    if _type:
        type_name = TYPE_LIST[_type] if _type in TYPE_LIST.keys() else _type

    if side:
        side = SIDE_LIST[side] if side in SIDE_LIST.keys() else side

    if fn:
        fn = TYPE_LIST[fn] if fn in TYPE_LIST.keys() else fn

    # rearrange this for different naming convention
    for q in [side, name, fn, type_name]:
        if q is None or q == '' or q == 'transform':
            continue

        if "|" in q:
            q = q.split('|')[-1]

        if not isinstance(q, basestring):
            str_list.append('{}'.format(q))
            continue

        str_list.append(q)

    if create:
        if _type == 'group':
            _type = 'transform'

        # find node before creation
        if find:
            objs = pm.ls('_'.join(str_list))
            if objs:
                for obj in objs:
                    shps = objs.getShapes()
                    if obj.type() == _type:
                        return obj
                    if shps:
                        for shp in shps:
                            if shp.type() == _type:
                                return obj

        obj = pm.createNode(_type, name='_'.join(str_list))

        # if obj is shape node, rename and return parent instead
        if isinstance(obj, pm.nodetypes.Shape):
            name = obj.name()
            obj.rename(obj.name() + 'Shape')
            obj_prnt = obj.getParent()
            obj_prnt.rename(name)
            return obj.getParent()

        return obj
    return '_'.join(str_list)


def group_pivot(obj, layer=None, world=True):
    """
    create group(s) as parents for given object
    :param obj: single object
    :param layer: suffix for group(s), must be in list
    :param world: parent group under world
    :return: created groups
    """
    if layer is None:
        layer = [TYPE_LIST['nul'], TYPE_LIST['offset'], TYPE_LIST['sdk']]

    grps = []
    for lay in layer:
        # pm.group(name = '{}_{}_GRP'.format(obj.name(),lay),em=1)
        if lay in TYPE_LIST.keys():
            lay = TYPE_LIST[lay]
        grp = create_name(side='', name=obj.name(), fn=lay, _type='group', create=True)
        if grps:
            grps[-1].addChild(grp)
        grps.append(grp)

    pm.delete(pm.parentConstraint(obj, grps[0]))
    pm.delete(pm.scaleConstraint(obj, grps[0]))

    # parent group to parent of obj
    if not world and obj.getParent():
        obj.getParent().addChild(grps[0])

    grps[-1].addChild(obj)
    return grps


def get_soft_selection_weight():
    # allDags, allComps, allOpacities = [], [], []
    #
    # # if soft select isn't on, return
    # if not pm.softSelect(q=True, sse=True):
    #     return allDags, allComps, allOpacities
    #
    # richSel = om.MRichSelection()
    # try:
    #     # get currently active soft selection
    #     om.MGlobal.getRichSelection(richSel)
    # except Exception:
    #     raise Exception('Error getting soft selection.')
    #
    # richSelList = om.MSelectionList()
    # richSel.getSelection(richSelList)
    # selCount = richSelList.length()
    #
    # for x in xrange(selCount):
    #     shapeDag = om.MDagPath()
    #     shapeComp = om.MObject()
    #     try:
    #         richSelList.getDagPath(x, shapeDag, shapeComp)
    #     except RuntimeError:
    #         # nodes like multiplyDivides will error
    #         continue
    #
    #     compOpacities = {}
    #     try:
    #         compFn = om.MFnSingleIndexedComponent(shapeComp)
    #     except:
    #         compFn = om.MFnDoubleIndexedComponent(shapeComp)
    #     try:
    #         # get the secret hidden opacity value for each component (vert, cv, etc)
    #         for i in xrange(compFn.elementCount()):
    #             weight = compFn.weight(i)
    #             u_ptr = om.MScriptUtil(0).asIntPtr()
    #             v_ptr = om.MScriptUtil(0).asIntPtr()
    #             compFn.getElement(i, u_ptr, v_ptr)
    #             compOpacities["{},{}".format(om.MScriptUtil(u_ptr).asInt(),
    #             om.MScriptUtil(v_ptr).asInt())] = weight.influence()
    #         print len(compOpacities.keys()), compOpacities
    #             # compOpacities[compFn.element(i)] = weight.influence()
    #     except Exception, e:
    #         print e.__str__()
    #         print 'Soft selection appears invalid, skipping for shape "%s".' % shapeDag.partialPathName()
    #
    #     allDags.append(shapeDag)
    #     allComps.append(shapeComp)
    #     allOpacities.append(compOpacities)
    #
    # return allDags, allComps, allOpacities

    """
     create and return a list of the soft selection weights
    """

    # temporary hack. Turn off symmetry when reading MRichSelection until I learn to use symmetry.
    # as far as my tests go, this maintains the symmetrical selection but reads it like a whole selection.
    # otherwise, only one half will be reading by MRichSelection. How does getSymmetry() work?
    symm_on = pm.symmetricModelling(q=True, symmetry=True)
    if symm_on:
        pm.symmetricModelling(e=True, symmetry=False)

    selection = om.MSelectionList()
    soft_sel = om.MRichSelection()
    om.MGlobal.getRichSelection(soft_sel)
    soft_sel.getSelection(selection)
    sel_count = selection.length()
    result = {}

    for sel in range(sel_count):
        shp_dag = om.MDagPath()
        shp_comp = om.MObject()

        try:
            selection.getDagPath(sel, shp_dag, shp_comp)
        except RuntimeError:
            # nodes like multiplyDivides will error
            continue

        # mesh object
        if shp_comp.apiTypeStr() == 'kMeshVertComponent':
            fn_comp = om.MFnSingleIndexedComponent(shp_comp)
            geo_iter = om.MItGeometry(shp_dag)
            point_count = geo_iter.exactCount()
            weight_array = [0.0] * point_count

        # surface object
        elif shp_comp.apiTypeStr() == 'kSurfaceCVComponent':
            fn_comp = om.MFnDoubleIndexedComponent(shp_comp)
            shp = om.MFnNurbsSurface(shp_dag.node())
            u_count = shp.numCVsInU()
            v_count = shp.numCVsInV()
            weight_array = [[0.0 for v in range(v_count)] for u in range(u_count)]

        # invalid object
        else:
            print "Invalid input."
            continue

        # find weights
        if fn_comp.hasWeights():
            for i in range(fn_comp.elementCount()):
                weight = round(fn_comp.weight(i).influence(), 3)
                if weight == 0:
                    continue
                if shp_comp.apiTypeStr() == 'kMeshVertComponent':
                    element = fn_comp.element(i)
                    weight_array[element] = weight

                elif shp_comp.apiTypeStr() == 'kSurfaceCVComponent':
                    u_ary = om.MIntArray()
                    v_ary = om.MIntArray()
                    fn_comp.getElements(u_ary, v_ary)

                    weight_array[u_ary[i]][v_ary[i]] = weight
        result[shp_dag.fullPathName().split("|")[-1]] = weight_array
    pm.symmetricModelling(e=True, symmetry=symm_on)
    return result


# def cv_array_to_1d(surface):
#     """
#     make cv to 1d list
#     :param surface:
#     :return:
#     """
#     if not surface.getShapes(type='nurbsSurface', ni=1):
#         print '{} does not contain nurbsSurface shape.'.format(surface)
#         return
#     cv_u = surface.cvsInU()
#     cv_v = surface.cvsInV()
#
#     return range(cv_u * cv_v)
#
#
# def array_to_cv(surface, array):
#     """
#     make a 1d array to become 2d array based on cv count on surface
#     :param surface:
#     :param array:
#     :return:
#     """
#     if not surface.getShapes(type='nurbsSurface', ni=1):
#         print '{} does not contain nurbsSurface shape.'.format(surface)
#         return
#     cv_u = surface.cvsInU()
#     cv_v = surface.cvsInV()
#
#     result = [range(cv_v)] * cv_u
#     u = 0
#     v = 0
#     for i in array:
#         result[u][v] = i
#         v += 1
#         if v > cv_v:
#             v = 0
#             u += 1
#     return result


def parent_to_no_touch(obj):
    grp_name = create_name(side='', name='noTouch', _type='group')
    if not pm.objExists(grp_name):
        no_touch = create_name(side='', name='noTouch', _type='group', create=True)
    else:
        no_touch = pm.PyNode(grp_name)

    pm.parent(obj, no_touch)


def extract_faces(vtxs):
    node = vtxs[0].node()

    new_node = pm.duplicate(node, rr=1)[0]
    vtx_ind = [v.currentItemIndex() for v in vtxs]
    new_vtx = [new_node.vtx[i] for i in vtx_ind]
    pm.select(pm.polyListComponentConversion(new_vtx, fv=True, tf=True))
    pm.select('{}.f[*]'.format(new_node), tgl=1)
    pm.delete()

    pm.parent(new_node, w=1)

    return new_node


def create_matrix_constrain(objs, maintain_offset=False, ignore=''):
    """
    create matrix constrain
    :param objs: list of object
    :param maintain_offset:
    :param ignore: 'trs'
    :return:
    """
    ignore = ignore.lower()

    parents = objs[:-1]
    target = objs[-1]

    # check if target has parent
    t_prnt = target.getParent()
    if not t_prnt:
        t_prnt = create_name(side='', name=target, fn='CONST', _type='group', create=True)
        pm.matchTransform(t_prnt, target)
        t_prnt.addChild(target)

    add_mat = create_name(side='', name=target, fn='matConst', _type='wtAddMatrix', create=True)

    invr_mat = create_name(side='', name=target, fn='matConst_prntInvr',  _type='multMatrix', create=True)
    add_mat.matrixSum.connect(invr_mat.matrixIn[0])
    t_prnt.worldInverseMatrix.connect(invr_mat.matrixIn[1])

    dcmp_mat = create_name(side='', name='{}_matConst'.format(target), _type='decomposeMatrix', create=True)
    invr_mat.matrixSum.connect(dcmp_mat.inputMatrix)

    weight = 1.0 / len(parents)

    for i, p in enumerate(parents):
        # create attribute to control weight
        attr_name = "{}_w".format(p)
        if attr_name not in pm.listAttr(target):
            target.addAttr(attr_name, at='double', min=0, dv=weight, k=1)
        name = "{}_p{}".format(target, i)
        mult_mat = create_name(side='', name=name, _type='multMatrix', create=True)

        # get offset
        if maintain_offset:
            offset = target.worldMatrix.get() * p.worldInverseMatrix.get()
            # off_mat = create_name(side='', name="temp", _type='multMatrix', create=True)
            # target.worldMatrix.connect(off_mat.matrixIn[0])
            # p.worldInverseMatrix.connect(off_mat.matrixIn[1])
            mult_mat.matrixIn[0].set(offset)

        p.worldMatrix.connect(mult_mat.matrixIn[1])
        mult_mat.matrixSum.connect(add_mat.wtMatrix[i].matrixIn)
        target.attr(attr_name).connect(add_mat.wtMatrix[i].weightIn)

    if 't' not in ignore:
        dcmp_mat.outputTranslate.connect(target.t, f=1)
    if 'r' not in ignore:
        # for joint orient
        if target.type() == 'joint':
            euler_quat = create_name(side='', name=target, fn='matConst', _type='eulerToQuat', create=True)
            target.jointOrient.connect(euler_quat.inputRotate)

            quat_invr = create_name(side='', name=target, fn='matConst', _type='quatInvert', create=True)
            euler_quat.outputQuat.connect(quat_invr.inputQuat)

            quat_prod = create_name(side='', name=target, fn='matConst', _type='quatProd', create=True)
            dcmp_mat.outputQuat.connect(quat_prod.input1Quat)
            quat_invr.outputQuat.connect(quat_prod.input2Quat)

            quat_euler = create_name(side='', name=target, fn='matConst', _type='quatToEuler', create=True)
            quat_prod.outputQuat.connect(quat_euler.inputQuat)
            quat_euler.outputRotate.connect(target.r, f=1)
        else:
            dcmp_mat.outputRotate.connect(target.r, f=1)
    if 's' not in ignore:
        dcmp_mat.outputScale.connect(target.s, f=1)

    return


def create_constrain_blend(obj, t=True, r=True):
    """
    create pair blend node
    :param obj: single object
    :param t:
    :param r:
    :return:
    """
    if not t and not r:
        pm.warning('==CONSTRAIN== Unable to create pairBlend for {}.'.format(obj))
        return

    if 'const_blend' not in pm.listAttr(obj):
        obj.addAttr('const_blend', at='double', min=0, max=1, k=1)

    pb_node = create_name(side='', name=obj, _type='pairBlend', create=True)
    obj.const_blend.connect(pb_node.weight)
    if obj.t.inputs():
        obj.t.insertInput(pb_node, 'ot', 'it2')
    else:
        for at in 'xyz':
            if obj.attr('t'+at).inputs():
                obj.attr('t'+at).insertInput(pb_node, 'ot{}'.format(at), 'it{}2'.format(at))

    if obj.r.inputs():
        obj.r.insertInput(pb_node, 'or', 'ir2')
    else:
        for at in 'xyz':
            if obj.attr('r' + at).inputs():
                obj.attr('r' + at).insertInput(pb_node, 'or{}'.format(at), 'ir{}2'.format(at))

    pb_node.it1.set(pb_node.it2.get())
    pb_node.ir1.set(pb_node.ir2.get())
    if not t:
        pb_node.txm.set(2)
        pb_node.tym.set(2)
        pb_node.tzm.set(2)
    if not r:
        pb_node.rm.set(2)

    pm.select(obj)
    return pb_node


def create_curve(objs, name='temp', degree=3):
    """
    create curve based on objs world positions
    :param objs:
    :param name:
    :param degree:
    :return: curve's transform
    """
    pnts = []

    new_jnts = objs[::1]
    if degree == 3:
        loc_a = pm.spaceLocator()
        objs[0].addChild(loc_a)
        pm.matchTransform(loc_a, objs[1])
        loc_a.t.set([q * .2 for q in loc_a.t.get()])

        loc_b = pm.spaceLocator()
        objs[-2].addChild(loc_b)
        pm.matchTransform(loc_b, objs[-1])
        loc_b.t.set([q * .8 for q in loc_b.t.get()])

        new_jnts.insert(1, loc_a)
        new_jnts.insert(-1, loc_b)

    # get world position list
    for j in new_jnts:
        pnts.append([round(q, 3) for q in pm.xform(j, q=1, ws=1, t=1)])
    if degree == 3:
        pm.delete(loc_b, loc_a)

    new_name = create_name(side='', name=name, _type='curve')
    ik_crv = pm.curve(d=degree, p=pnts, name=new_name)
    return ik_crv


def create_space_attr(target, parents=['loc1', 'loc2'], nice_name=None, con=None):
    # check con
    if con is None or not pm.ls(con):
        print '==SPACE== Please specify "con"'
        return

    # # validate parents
    # for p in parents:
    #     if not pm.ls(p):
    #         print '==SPACE== Parents input invalid. Object does not exist.'
    #         return

    # check nice name
    if nice_name is None:
        nice_name = parents
    else:
        if len(nice_name) != len(parents):
            print '==SPACE== Amount of "nice_name" does not same as amount of "parents"'
            return

    # check attribute
    if 'space' not in pm.listAttr(con, ud=1):
        con.addAttr('space', at='enum', en=nice_name, k=1)
    else:
        print '==SPACE== "Space" attribute already exists in {}.'.format(con)
        return

    # check groups
    space_main = create_name(side='', name='space', _type='group', create=False)
    if not pm.ls(space_main):
        space_main = create_name(side='', name='space', _type='group', create=True)
    else:
        space_main = space_main

    space_grp = create_name(side='', name=con, fn='space', _type='group', create=False)
    if not pm.ls(space_grp):
        space_grp = create_name(side='', name=con, fn='space', _type='group', create=True)
        pm.parent(space_grp, space_main)
    else:
        space_grp = space_grp

    # create locator
    locs = []
    for i, p in enumerate(parents):
        loc = create_name(side='', name=con, fn='space_{}'.format(nice_name[i]), _type='transform', create=True)
        if pm.ls(p):
            pm.parentConstraint(p, loc)
        pm.parent(loc, space_grp)
        locs.append(loc)

    # create constraint node
    const = pm.parentConstraint(locs, target, mo=1)

    for i, w in enumerate(const.getWeightAliasList()):
        ends = len(str(len(const.getWeightAliasList()))) + 1
        cond = create_name(side='', name=w.attrName(longName=1)[:(-1 * ends)], _type='condition', create=True)

        con.space.connect(cond.firstTerm)
        cond.secondTerm.set(i)
        cond.colorIfTrue.set([1, 0, 0])
        cond.colorIfFalse.set([0, 0, 0])

        cond.outColorR.connect(w)

    pm.select(con)
    return space_grp


def create_closest_poci(objs, prefix='', locator=True):
    """
    :param locator: Optional, create driven locator. Return lis
    :param prefix: Optional, add prefix in created name
    :param objs: [obj(s), crv], curve always in last position
    :return: [created nodes]. Return list of locator if locator parameter is True.
    """
    crv = objs[-1]
    objs = objs[:-1]
    nodes = []
    for obj in objs:
        pos = pm.xform(obj, q=1, ws=1, t=1)
        poci = create_name(side='', name=obj, fn=prefix, _type='pointOnCurveInfo', create=True)
        crv.worldSpace.connect(poci.inputCurve)
        param = crv.getParamAtPoint(crv.closestPoint(pos))
        poci.parameter.set(param)
        if locator:
            loc = create_name(side='', name=obj, fn=prefix, _type='locator', create=True)
            poci.position.connect(loc.t)
            nodes.append(loc)
            continue
        nodes.append(poci)
    return nodes


def move_shape(objs):
    """
    move shapes while maintaining its pivot
    :param objs:
    :return:
    """
    if len(objs) != 2:
        print 'Invalid objects. Only accept two objects [object, destination].'
        return
    piv_loc = pm.spaceLocator()
    pm.matchTransform(piv_loc, objs[0])

    pm.matchTransform(objs[0], objs[1], pos=1)
    pm.makeIdentity(objs[0], a=1, t=1)
    pm.matchTransform(objs[0], piv_loc, piv=1)
    pm.delete(piv_loc)
    return


def duplicate_and_move(objs, replace_key=['joint', 'ctrl'], groups=['offset']):
    """
    duplicate last object and move to targets
    :param groups:
    :param replace_key:
    :param objs:
    :return:
    """
    output = []
    dup = objs[-1]
    for q in objs[:-1]:
        # check name
        new_name = replace_name(q.name(), replace_key[0], replace_key[1])
        if new_name == q.name():
            new_name = "dul_{}".format(new_name)

        # duplicate
        new_dup = pm.duplicate(dup, name=new_name)

        # add group
        new_dup_grp = group_pivot(new_dup[0], layer=groups)
        new_dup_grp.extend(new_dup)

        pm.matchTransform(new_dup_grp[0], q)

        output.append(new_dup_grp)
    return output
