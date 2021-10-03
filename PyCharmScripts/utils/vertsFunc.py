import pymel.all as pm


def find_symmetric(vtxs, mirror_plane='YZ'):
    """
    Find symmetric verts from inputs
    :param vtxs: list of vertices
    :param mirror_plane: 'XY', 'YZ', 'XZ'
    :return:
    """
    sym_list = {}
    tmp = pm.spaceLocator()
    for vt in vtxs:
        shape = vt.node()

        vt_pos = vt.getPosition(space='world')
        if mirror_plane == 'XY':
            vt_pos[2] = vt_pos[2] * -1
        elif mirror_plane == 'XZ':
            vt_pos[1] = vt_pos[1] * -1
        elif mirror_plane == 'YZ':
            vt_pos[0] = vt_pos[0] * -1
        tmp.t.set(vt_pos)

        mirror_vt = find_closest_point([tmp, shape.getParent()])

        # check mirror_vt is in value
        if mirror_vt not in sym_list.values():
            sym_list[vt] = mirror_vt
        else:
            print 'Unable to find symmetry point for {}'.format(vt)
            continue

    pm.delete(tmp)
    return sym_list


def find_closest_point(objs):
    """
    find closest vertex on mesh or curve
    :param objs: [object, mesh]
    :return:
    """
    if len(objs) != 2:
        print "Invalid inputs. Only accept [object, mesh]"
        return

    if not objs[1].getShapes(ni=1):
        print "Second object does not contain any shape."
        return

    pos = pm.xform(objs[0], q=1, ws=1, t=1)
    shape = objs[1].getShapes(ni=1)[0]

    # run
    if isinstance(shape, pm.Mesh):
        m_pos, face_id = shape.getClosestPoint(pos, space='world')
        verts_in_face = shape.getPolygonVertices(face_id)
        verts = sorted(verts_in_face, key=lambda vid: m_pos.distanceTo(shape.vtx[vid].getPosition(space='world')))
        return shape.vtx[verts[0]]

    if isinstance(shape, pm.NurbsCurve):
        m_pos = shape.closestPoint(pos, space='world')
        cvs = range(shape.numCVs())
        cvs = sorted(cvs, key=lambda vid: m_pos.distanceTo(shape.cv[vid].getPosition(space='world')))
        return shape.cv[cvs[0]]


def find_side_vtx(vtxs, axis='x'):
    """
    find vertices on furthest apart on x, y and z axis
    :param vtxs:
    :param axis: 'x', 'y' or 'z'. Find vertices closest to 0 on axis
    :return:
    """
    axis_index = {'x': 0, 'y': 1, 'z': 2}

    far = sorted(vtxs, key=lambda vid: vid.getPosition(space='world')[axis_index[axis]], reverse=True)
    zero = sorted(vtxs, key=lambda vid: abs(round(vid.getPosition(space='world')[axis_index[axis]], 3)))

    return {'far': [far[0], far[-1]],
            'zero': zero[0:2]}
