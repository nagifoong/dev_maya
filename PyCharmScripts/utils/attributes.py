import pymel.all as pm

def duplicate_attrs(objs, ignore=[], transfer_conn=False, bridge_mode=True):
    """
    duplicate attribute from source to target
    :param objs: [source, target]
    :param ignore: ignore attribute
    :param transfer_conn: transfer connection to new object
    :param bridge_mode: insert connection between source and destination
    :return:
    """
    sources = objs[:-1]
    target = objs[-1]
    for src in sources:
        for at in src.listAttr(ud=1):
            if at.attrName() in ignore:
                continue

            # store lock state
            lock = 0
            if at.isLocked():
                lock = 1
            at.set(l=0)

            # define attribute name
            if len(sources) > 1 or bridge_mode:
                at_name = "{}__{}".format(src, at.attrName())
            else:
                at_name = at.attrName()

            # float attribute
            if at.type() == 'double':
                target.addAttr(at_name, at='double', dv=at.get(), k=1)
                if at.getMin() is not None:
                    target.attr(at_name).setMin(at.getMin())
                if at.getMax() is not None:
                    target.attr(at_name).setMax(at.getMax())

            # enum attribute
            elif at.type() == 'enum':
                enum_list = sorted(at.getEnums().items(), key=lambda x: x[1])
                en_str = ":".join([q[0] for q in enum_list])
                target.addAttr(at_name, at='enum', en=en_str, k=1)
                target.attr(at_name).set(at.get())

            # boolean attribute
            elif at.type() == 'bool':
                target.addAttr(at_name, at='bool', k=1)
                target.attr(at_name).set(at.get())

            # string attribute
            elif at.type() == 'string':
                target.addAttr(at_name, dt='string', k=1)

            # if transfer_conn or bridge_mode
            # run these code
            if transfer_conn or bridge_mode:
                inps = at.inputs(p=1)
                for inp in inps:
                    if bridge_mode:
                        inp.insertInput(target, at_name, at_name)
                    inp.connect(at.attr(at_name))
                outs = at.outputs(p=1)
                for out in outs:
                    if out.isLocked():
                        out.set(l=0)
                    target.attr(at_name).connect(out, f=1)
                    at.connect(target.attr(at_name), f=1)

            # lock attribute
            if lock:
                target.attr(at_name).set(l=1)


def create_attr(obj, name='temp', **karg):
    if name in pm.listAttr(obj, ud=1):
        return obj.attr(name)
    return obj.addAttr(name, **karg)


def copy_attr(src, target):
    duplicate_attrs([src, target], bridge_mode=False)
    for at in src.listAttr(ud=1):
        if at.isSettable:
            target.attr(at.attrName()).connect(at)
