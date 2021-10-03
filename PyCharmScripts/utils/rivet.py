import pymel.all as pm
from PySide2 import QtWidgets

from PyCharmScripts.utils import vertsFunc, common, channels
from PyCharmScripts.tools.controllerShape import main as shape_gen
from ..data import color_data, name_data
import ui_utils

reload(color_data)
reload(name_data)
reload(channels)
reload(common)
reload(ui_utils)

SIDE_LIST = name_data.SIDE_LIST
TYPE_LIST = name_data.TYPE_LIST
SIDE_COLOR = color_data.SIDE_COLOR
COLOR_DICT = color_data.COLOR_DICT


def create_obj_attach_mesh(vtxs, joint=False, prefix='attachMeshTemp', find_symmetry=True,
                           test=False, nullify='', con_shape='locator', con_scale=1, constrain=False):
    """
    create object and attach to mesh. Rivet on mesh
    :param constrain: constrain or direct connect joints
    :param vtxs: [list of vertices]
    :param joint: boolean, create joint
    :param prefix: prefix for created objects by this function
    :param find_symmetry: boolean, find symmetry vertices
    :param test: boolean, test mode
    :param nullify: object to make controllers follow its rotation and scale value
    :param con_shape: shape of controllers
    :param con_scale: size of controllers shape
    :return:
    """
    vtxs = pm.ls(vtxs, fl=1)
    jnt_main_grp = None

    """define groups"""
    # util group
    grp_name = common.create_name(side='', name='attachMesh', fn='util', _type='group')
    if not pm.objExists(grp_name):
        util_grp = common.create_name(side='', name='attachMesh', fn='util', _type='group', create=True)
        util_grp.v.set(0)
    else:
        util_grp = pm.PyNode(grp_name)

    common.parent_to_no_touch(util_grp)

    # curve group
    grp_name = common.create_name(side='', name='attachMesh', fn='curve', _type='group')
    if not pm.objExists(grp_name):
        crv_grp = common.create_name(side='', name='attachMesh', fn='curve', _type='group', create=True)
        util_grp.addChild(crv_grp)
    else:
        crv_grp = pm.PyNode(grp_name)

    # controller group
    grp_name = common.create_name(side='', name='attachMesh', fn='ctrl', _type='group')
    if not pm.objExists(grp_name):
        con_main_grp = common.create_name(side='', name='attachMesh', fn='ctrl', _type='group', create=True)
    else:
        con_main_grp = pm.PyNode(grp_name)

    # joint group
    if joint:
        # define group name
        grp_name = common.create_name(side='', name='attachMesh', fn='joint', _type='group')

        if not pm.objExists(grp_name):
            jnt_main_grp = common.create_name(side='', name='attachMesh', fn='joint', _type='group', create=True)
            if not constrain:
                util_grp.addChild(jnt_main_grp)
        else:
            jnt_main_grp = pm.PyNode(grp_name)

    # variable
    jnt_grps = []
    jnts = []
    con_grps = []
    cons = []
    name_list = ["{}_{}".format(vtx.node(), vtx.currentItemIndex()) for vtx in vtxs]
    crvs = []

    # if prefix is given
    if prefix:
        name_list = []
        for ind, vtx in enumerate(vtxs):
            suffix = str(ind + 1).zfill(len(str(len(vtxs) + 1)))
            if len(vtx) == 1 and not find_symmetry:
                name_list.append(prefix)
            else:
                name_list.append("{}_{}".format(prefix, suffix))

    """object rotation"""
    # nullify main group
    grp_name = common.create_name(side='', name='attachMesh', fn='nullify', _type='group')
    if not pm.objExists(grp_name):
        null_grp = common.create_name(side='', name='attachMesh', fn='nullify', _type='group', create=True)
        util_grp.addChild(null_grp)
    else:
        null_grp = pm.PyNode(grp_name)

    if nullify:
        grp_name = common.create_name(side='', name=nullify, fn='transform_nullify', _type='group')
        if not pm.objExists(grp_name):
            null = common.create_name(side='', name=nullify, fn='transform_nullify', _type='group', create=True)
            null_grp.addChild(null)
            pm.parentConstraint(nullify, null, mo=1)
            pm.scaleConstraint(nullify, null, mo=1)
        else:
            null = pm.PyNode(grp_name)
    else:
        grp_name = common.create_name(side='', name='transform', fn='nullify', _type='group')
        if not pm.objExists(grp_name):
            null = common.create_name(side='', name='transform', fn='nullify', _type='group', create=True)
            null_grp.addChild(null)
        else:
            null = pm.PyNode(grp_name)

    """find symmetric"""
    if find_symmetry:
        symm_list = vertsFunc.find_symmetric(vtxs, mirror_plane='YZ')
        vtxs = []
        name_list = []
        m_count = 1
        side_count = 1
        padding = len(str(len(symm_list.keys()) + 1))

        for key in symm_list.keys():
            # when key and value is same item
            # middle object
            if key == symm_list[key]:
                vtxs.append(key)
                new_name = '{}_edge_{}'.format(key.node(), key.currentItemIndex())
                if prefix:
                    new_name = '{}_{}_{}'.format(SIDE_LIST['middle'], prefix, str(m_count).zfill(padding))
                name_list.append(new_name)
                m_count += 1
                continue

            for ind, indv in enumerate([key, symm_list[key]]):
                vtxs.append(indv)
                new_name = '{}_edge_{}'.format(key.node(), key.currentItemIndex())
                if prefix:
                    new_name = '{}_{}'.format(prefix, str(side_count).zfill(padding))

                # find position for left and right side
                if round(indv.getPosition(space='world')[0], 3) > 0:
                    new_name = '{}_{}'.format(SIDE_LIST['left'], new_name)
                else:
                    new_name = '{}_{}'.format(SIDE_LIST['right'], new_name)
                name_list.append(new_name)
            side_count += 1

        # if only has one object, remove numbering
        if m_count == 2:
            name_list = ['_'.join(name.split("_")[:-1]) if name[0] == SIDE_LIST['middle'] else name
                         for name in name_list]
        if side_count == 2:
            name_list = ['_'.join(name.split("_")[:-1]) if name[0] == SIDE_LIST['left'] or name[0] == SIDE_LIST['right']
                         else name for name in name_list]

    # test mode
    if test:
        print len(name_list), name_list
        print len(vtxs), vtxs
        for i, vtx in enumerate(vtxs):
            loc = pm.spaceLocator(name=name_list[i])
            pm.xform(loc, t=vtx.getPosition(space='world'))
        return

    """create controllers"""
    for ind, vtx in enumerate(vtxs):
        # flatten edge list and use the first edge
        edge = pm.ls(pm.polyListComponentConversion(vtx, fv=True, te=True), fl=1)[0]
        temp_name = name_list[ind]
        mirror = True if temp_name.split("_")[0] == SIDE_LIST['right'] else False

        crv, node = [pm.PyNode(q) for q in pm.polyToCurve(edge, form=2, degree=1,
                                                          name='{}_edge_{}'.format(temp_name, TYPE_LIST['curve']))]
        crv_grp.addChild(crv)
        crvs.append(crv)
        node.rename('{}_edge_{}'.format(prefix, TYPE_LIST['polyEdgeToCurve']))

        poci = common.create_name(side='', name=temp_name, _type='pointOnCurveInfo', create=True)
        poci.turnOnPercentage.set(1)
        crv.getShapes(ni=0)[0].worldSpace.connect(poci.inputCurve)

        if round(vtx.getPosition(space='world')[0], 3) != round(poci.position.get()[0], 3):
            poci.parameter.set(1)

        con_name = common.create_name(side='', name=temp_name, _type='ctrl')

        # coloring
        side = temp_name.split("_")[0]
        color_name = SIDE_COLOR['middle']
        if side == SIDE_LIST['left']:
            color_name = SIDE_COLOR['left']
        elif side == SIDE_LIST['right']:
            color_name = SIDE_COLOR['right']

        # create controllers
        con_struc = shape_gen.create(con_shape, name=con_name, groups=['pos', 'mirror', 'offset', 'sub'],
                                     color=COLOR_DICT[color_name])

        con_struc[-1].s.set([con_scale] * 3)
        pm.makeIdentity(con_struc[-1], a=1, t=0, r=0, s=1)

        poci.position.connect(con_struc[0].t)
        con_struc[0].addAttr('parameter', at='double', min=0, max=100, dv=poci.parameter.get() * 100, k=1)

        uc = common.create_name(side='', name=temp_name, fn='edge', _type='unitConversion', create=True)
        uc.conversionFactor.set(.01)
        uc.output.connect(poci.parameter)
        con_struc[0].parameter.connect(uc.input)

        minus = common.create_name(side='', name=temp_name, fn='edge_minus', _type='plusMinusAverage', create=True)
        minus.operation.set(2)
        minus.input3D[0].set(con_struc[-1].t.get())
        con_struc[-1].t.connect(minus.input3D[1])
        minus.output3D.connect(con_struc[-2].t)

        con_main_grp.addChild(con_struc[0])
        con_grps.append(con_struc[0])
        cons.append(con_struc[-1])

        # mirror behavior on right side
        if mirror:
            con_struc[1].sx.set(-1)

        null.r.connect(con_struc[0].r)
        null.s.connect(con_struc[0].s)

        # lock channels
        channels.cb_status([con_struc[1]], translates='xyz', rotates='xyz', lock=1)
        channels.cb_status([con_struc[2]], scales='xyz', lock=1)

        # create joint which controlled by controller
        if joint:
            jnt = common.create_name(side='', name=temp_name, _type='joint', create=True)
            jnt_grps = common.group_pivot(jnt, layer=['nul', 'mirror', 'offset', 'pxy', 'nul_rot'])
            jnt_grps[0].t.set(con_struc[0].t.get())

            con_struc[1].s.connect(jnt_grps[1].s)
            con_struc[-3].r.connect(jnt_grps[2].r)
            # nullify rotate offset
            jnt_grps[4].ro.set(5)
            for at in 'xyz':
                uc = common.create_name(side='', name=jnt, fn='nul_rot'+at.upper(), _type='unitConversion', create=True)
                uc.conversionFactor.set(-1)
                jnt_grps[2].attr('r'+at).connect(uc.input)
                uc.output.connect(jnt_grps[4].attr('r'+at))

            for at in 'trs':
                con_struc[-1].attr(at).connect(jnt_grps[3].attr(at))

            jnt_main_grp.addChild(jnt_grps[0])
            jnt_grps.append(jnt_grps[0])
            jnts.append(jnt)

            channels.cb_status([jnt_grps[1]], translates='xyz', rotates='xyz', lock=1)
            channels.cb_status([jnt_grps[2]], scales='xyz', lock=1)
            channels.cb_status([jnt], all=1, lock=1)
    if joint:
        return {'con_main': con_main_grp,
                'pos_grps': con_grps,
                'cons': cons,
                'jnt_grps': jnt_grps,
                'jnts': jnts,
                'curves': crvs}

    return {'con_main': con_main_grp,
            'pos_grps': con_grps,
            'cons': cons,
            'curves': crvs}


class RivetUI(QtWidgets.QDialog):
    def __init__(self, parent=ui_utils.get_maya_window()):
        super(RivetUI, self).__init__(parent=parent)
        self.ui_name = 'CreateRivetUI'
        self.setWindowTitle('Create Rivet UI')

        self.create_widget()
        self.create_connection()

        # ui_utils.ui_geom_setting(self, ui_name=self.ui_name, load=True)
        self.show()

    def create_widget(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        name_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('Prefix:')
        self.name_line_edit = QtWidgets.QLineEdit('temp')
        name_layout.addWidget(label)
        name_layout.addWidget(self.name_line_edit)
        main_layout.addLayout(name_layout)

        self.jnt_check_box = QtWidgets.QCheckBox('Create Joint(s)\t')
        self.jnt_check_box.setChecked(True)
        main_layout.addWidget(self.jnt_check_box)

        self.find_sym_check_box = QtWidgets.QCheckBox('Find Symmetry\t')
        self.find_sym_check_box.setChecked(True)
        main_layout.addWidget(self.find_sym_check_box)

        bt_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(bt_layout)
        self.create_bt = QtWidgets.QPushButton('Create')
        bt_layout.addWidget(self.create_bt)
        self.cancel_bt = QtWidgets.QPushButton('Cancel')
        bt_layout.addWidget(self.cancel_bt)

    def create_connection(self):
        self.create_bt.clicked.connect(self.create_bt_func)
        self.cancel_bt.clicked.connect(self.close)

    def closeEvent(self, event):
        # ui_utils.ui_geom_setting(self, ui_name=self.ui_name, save=True)
        QtWidgets.QDialog.closeEvent(self, event)

    def create_bt_func(self):
        sel = pm.selected()
        # make sure selection is vertex only.
        for s in sel:
            if not isinstance(s, pm.MeshVertex):
                pm.warning('==RIVET== Selection is invalid.')
                return
        prefix = self.name_line_edit.text()
        j = self.jnt_check_box.isChecked()
        f = self.find_sym_check_box.isChecked()
        with pm.UndoChunk():
            create_obj_attach_mesh(sel, joint=j, prefix=prefix, find_symmetry=f, nullify='', con_shape='cube')
        pm.setAttr('attachMesh_util_grp.v', 1)
        return


def get_rivet_window():
    """call RivetDialog"""
    global dialog_rivet
    try:
        dialog_rivet.close()
        dialog_rivet.deleteLater()
    except Exception as ew:
        a = ew

    dialog_rivet = RivetUI()
    return dialog_rivet