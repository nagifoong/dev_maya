import pymel.all as pm


def cb_status(objs, all=0, translates='', rotates='', scales='', v=0, lock=1, show=0):
    """
    condition : (lock,hidden),(unlock,show)
    :param objs:
    :param all:
    :param translates:
    :param rotates:
    :param scales:
    :param v:
    :param lock:
    :param show:
    :return:
    """
    if not objs:
        pm.warning('Please select at least one object.')
        return
    if all:
        translates = 'xyz'
        rotates = 'xyz'
        scales = 'xyz'

    if isinstance(objs, pm.PyNode):
        objs = [objs]

    for obj in objs:
        if obj.type() not in ['transform', 'joint']:
            pm.warning('{} is not a valid object.'.format(obj.name()))
            continue
        # lock
        if lock:
            for at in 'xyz':
                if at in translates:
                    obj.attr('t' + at).set(l=lock, k=show)
                if at in rotates:
                    obj.attr('r'+at).set(l=lock, k=show)
                if at in scales:
                    obj.attr('s'+at).set(l=lock, k=show)
            if v:
                obj.v.set(l=lock, k=show)

        # unlock and show
        elif not lock and show:
            for at in 'xyz':
                if at in translates:
                    obj.attr('t' + at).set(l=lock, cb=show)
                    obj.attr('t' + at).set(k=show)
                if at in rotates:
                    obj.attr('r' + at).set(l=lock, cb=show)
                    obj.attr('r' + at).set(k=show)
                if at in scales:
                    obj.attr('s' + at).set(l=lock, cb=show)
                    obj.attr('s' + at).set(k=show)
            if v:
                obj.v.set(l=lock, cb=show)
                obj.v.set(k=show)
