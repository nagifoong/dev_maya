import pymel.all as pm

import name_data

TYPE_LIST = name_data.TYPE_LIST


def create_name(side='m', name='default', fn='', type='group', create=False, argv={}):
    str_list = []
    if type:
        type = TYPE_LIST[type]

    # rearrange this for different naming convention
    name_list = [side, name, fn, type]

    for q in name_list:
        if q is None or q == '':
            continue
        str_list.append(q)
        
    if create:
        obj = pm.createNode(type, name='_'.join(str_list), **argv)
        return obj
    return '_'.join(str_list)
