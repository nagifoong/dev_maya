import pickle
import os
import sys
from functools import partial
import pymel.all as pm
import maya.mel as mel
from PySide2 import QtWidgets, QtGui
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

import ui_utils
from ..data import name_data

py_version = sys.version.split(' ')[0]
if not py_version.startswith('2'):
    long = int
    from importlib import reload

reload(ui_utils)
reload(name_data)

PROJECT_DIR = pm.workspace(q=1, dir=1)


def get_skin_cluster(node):
    """
    find skin cluster node
    :param node:
    :return:
    """

    scl = mel.eval('findRelatedSkinCluster("{}")'.format(node))
    if scl:
        return pm.PyNode(scl)
    else:
        # try using its parent
        scl = mel.eval('findRelatedSkinCluster("{}")'.format(node.node()))
        if scl:
            return pm.PyNode(scl)
        print "=SKIN= Unable to find skin cluster node on {}".format(node)
        return None


def create_scl(*argv, **kargv):
    """
    Create skin cluster with proper naming
    :param argv: [mesh, jnts]
    :return:
    """

    if len(argv) < 2:
        if isinstance(argv[0], list):
            argv = argv[0]
        else:
            print "=SKIN= Invalid input. Expecting more than 2 inputs."
            return
    scl = pm.skinCluster(*argv, toSelectedBones=True, mi=2, **kargv)
    geom = scl.getGeometry()[0].getParent()
    scl.rename("{}_{}".format(geom, name_data.TYPE_LIST['skinCluster']))
    return scl


def copy_skin(args, one_to_one=False):
    """
    Copy skin cluster, create new skin cluster if target is not skinned.
    :param args: object needed to copy skin weight from source
    :param one_to_one: source and target must have same vertices count
    :return:
    """
    source = args[0]
    args = args[1:]
    source_scl = get_skin_cluster(source)
    new_scl = []
    if not source_scl:
        print "=SKIN= Operation stopped. {} does not have any skinning.".format(source)
        return

    # get skin cluster parameter
    jnts = source_scl.influenceObjects()
    skn_method = source_scl.getSkinMethod()
    for target in args:
        scl = get_skin_cluster(target)
        if not scl:
            scl = create_scl(target, jnts)
            scl.skinningMethod.set(skn_method)

        if not one_to_one:
            pm.copySkinWeights(source, target, noMirror=True, surfaceAssociation='closestPoint',
                               influenceAssociation=['name', 'label', 'oneToOne'], normalize=True)
        else:
            # maybe add condition to make sure vertices or cv counts are same with source
            weights = source_scl.getWeights(source)
            weight_array = []
            for w in weights:
                weight_array.extend(w)
            scl.setWeights(target.getShapes(ni=1)[0], range(len(jnts)), weight_array, False)
        new_scl.append(scl)

    return new_scl
    # bld_weight = {}
    # for v in pm.ls(source.vtx, fl=1):
    #     bld_weight[v.currentItemIndex()] = scl.getBlendWeights(source, v)


def copy_crv_weight(source, target):
    """
    copy skin weight from source(curve) to target(surface)
    :param source:
    :param target:
    :return:
    """
    source_scl = get_skin_cluster(source)
    jnts = source_scl.getInfluence()

    # create skin cluster
    target_scl = get_skin_cluster(target)
    if target_scl:
        target_scl.unbind()
    scl = pm.skinCluster(target, jnts, name='{}_SCL'.format(target), tsb=True)
    weights = source_scl.getWeights(source)

    # copy weight
    weights = [q for q in weights] * 2

    weight_array = []
    for w in weights:
        weight_array.extend(w)

    scl.setWeights(target.getShapes(ni=1)[0], range(len(jnts)), weight_array, False)
    return scl


def export_skins(objs, folder_path=PROJECT_DIR + "/skinWeight/"):
    """
    export skin weight as files
    :param objs: obj(s) selection
    :param folder_path: folder path to store exported files
    :return:
    """
    # validate folder path
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for obj in objs:
        # make sure obj is transform node
        if not isinstance(obj, pm.Transform):
            obj = obj.getParent()
        file_name = "{}.sw".format(obj.replace("|", "_-_"))
        result_data = {}

        # validate skin cluster
        scl = get_skin_cluster(obj)
        if not scl:
            continue

        # data gathering
        result_data['joint'] = [j.name() for j in scl.influenceObjects()]
        geom = scl.getGeometry()[0]
        if isinstance(geom, pm.Mesh):
            result_data['blend_weight'] = scl.getBlendWeights(obj, obj.vtx)
        elif isinstance(geom, pm.NurbsSurface) or isinstance(geom, pm.NurbsCurve):
            result_data['blend_weight'] = scl.getBlendWeights(obj, obj.cv)
        else:
            "=SKIN= Export skin weight does not support {}.".format(geom.type())
            continue
        weights = [w for w in scl.getWeights(obj)]
        result_data['weights'] = []
        for w in weights:
            result_data['weights'].extend([round(q, 4) for q in w])
        result_data['skin_method'] = scl.skinningMethod.get()
        result_data['maintain_max_influence'] = scl.mmi.get()
        result_data['max_influence'] = scl.mi.get()
        # print result_data

        # save file
        pickle.dump(result_data, open(folder_path + file_name, 'w'))
        print "=SKIN= Exported skin weight from {} to {}/{}.".format(obj, folder_path, file_name)
    return


def import_skin(obj, file_path=''):
    """
    import skin to obj. Only work for one object per run
    :param obj:
    :param file_path:
    :return:
    """
    # validate folder path
    if not os.path.exists(file_path):
        print "=SKIN= Given path does not exist."
        return

    if isinstance(obj, list):
        obj = obj[0]

    if not isinstance(obj, pm.PyNode):
        obj = pm.PyNode(obj)

    result = {}
    with (open(file_path, 'rb')) as opened:
        # while True:
        try:
            result = pickle.load(opened)
        except Exception as e:
            print e

    # check verts count
    if isinstance(obj.getShapes(ni=1)[0], pm.Mesh):
        count = obj.numVertices()
    elif isinstance(obj.getShapes(ni=1)[0], pm.NurbsSurface) or isinstance(obj.getShapes(ni=1)[0], pm.NurbsCurve):
        count = len(pm.ls(obj.cv, fl=1))
    else:
        print "=SKIN= Import skin weight does not support {}.".format(obj.getShapes(ni=1)[0].type())
        return

    if count != (len(result['weights']) / len(result['joint'])):
        print '=SKIN= Object vertex or cv count is not same as file.'
        return

    # unbind skin
    scl = get_skin_cluster(obj)
    if scl:
        scl.unbind()

    # create joint if missing
    for jnt in result['joint']:
        if not pm.ls(jnt):
            pm.select(cl=1)
            pm.joint(name=jnt)
            print '=SKIN= Missing joint {}. Creating a joint on origin.'.format(jnt)

    scl = create_scl(result['joint'], obj)

    # set attributes
    scl.setWeights(obj.getShapes(ni=1)[0], range(len(result['joint'])), result['weights'], False)

    if isinstance(obj.getShapes(ni=1)[0], pm.Mesh):
        scl.setBlendWeights(obj, obj.vtx, result['blend_weight'])
    elif isinstance(obj.getShapes(ni=1)[0], pm.NurbsSurface) or isinstance(obj.getShapes(ni=1)[0], pm.NurbsCurve):
        scl.setBlendWeights(obj, obj.cv, result['blend_weight'])
    else:
        print "=SKIN= Import skin weight does not support {}.".format(obj.getShapes(ni=1)[0].type())

    scl.setBlendWeights(obj.getShapes(ni=1)[0], obj.vtx, result['blend_weight'])
    scl.skinningMethod.set(result['skin_method'])
    scl.mmi.set(result['maintain_max_influence'])
    scl.mi.set(result['max_influence'])
    print '=SKIN= Successfully import skin weight on {}.'.format(obj)
    return


class SkinDialog(QtWidgets.QDialog):
    def __init__(self, parent=ui_utils.get_maya_window()):
        super(SkinDialog, self).__init__(parent)
        self.ui_name = 'SkinImportExportUI'
        self.setWindowTitle('Import Export Skin weights')

        self.create_widget()
        self.create_connections()

        self._update_list_widget()

        ui_utils.ui_geom_setting(self, ui_name=self.ui_name, load=True)
        self.show()

    def closeEvent(self, event):
        ui_utils.ui_geom_setting(self, ui_name=self.ui_name, save=True)
        QtWidgets.QDialog.closeEvent(self, event)

    def create_widget(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        path_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(path_layout)

        path_label = QtWidgets.QLabel('Folder Path:')
        path_layout.addWidget(path_label)

        self.path_line = QtWidgets.QLineEdit()
        proj_path = pm.workspace(q=1, dir=1)
        sw_folder = "{}/skinWeight/".format(proj_path)
        if os.path.exists(sw_folder):
            self.path_line.setText(sw_folder)
        else:
            self.path_line.setText(proj_path)
        self.path_line.setReadOnly(True)
        path_layout.addWidget(self.path_line)

        self.path_bt = QtWidgets.QPushButton('..')
        path_layout.addWidget(self.path_bt)

        self.refresh_bt = QtWidgets.QPushButton()
        self.refresh_bt.setIcon(QtGui.QIcon(':/redrawPaintEffects.png'))
        path_layout.addWidget(self.refresh_bt)

        self.file_widget = QtWidgets.QListWidget()
        self.file_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        main_layout.addWidget(self.file_widget)

        info_label = QtWidgets.QLabel('** Import based on file name. ')
        main_layout.addWidget(info_label)

        bts_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(bts_layout)

        self.exp_bt = QtWidgets.QPushButton('Export')
        bts_layout.addWidget(self.exp_bt)

        self.imp_bt = QtWidgets.QPushButton('Import')
        bts_layout.addWidget(self.imp_bt)

        self.cancel_bt = QtWidgets.QPushButton('Cancel')
        bts_layout.addWidget(self.cancel_bt)

    def create_connections(self):
        self.refresh_bt.clicked.connect(self._update_list_widget)
        self.path_bt.clicked.connect(self.get_folder_path)
        self.exp_bt.clicked.connect(self.export_skin_func)
        self.imp_bt.clicked.connect(self.import_skin_func)
        self.cancel_bt.clicked.connect(self.close)

    def get_folder_path(self):
        file_dialog = pm.fileDialog2(dir=self.path_line.text(), fm=2, okc='Set')
        if file_dialog:
            self.path_line.setText('{}/'.format(file_dialog[0]))
            self._update_list_widget()

    def _update_list_widget(self):
        self.file_widget.clear()

        folder = pm.util.path(self.path_line.text())
        files = folder.files('*.sw')
        for f in files:
            item = QtWidgets.QListWidgetItem(f.replace(folder, ''))
            self.file_widget.addItem(item)

    def export_skin_func(self):
        sel = pm.selected()
        export_skins(sel, folder_path=self.path_line.text())
        self._update_list_widget()
        return

    def import_skin_func(self):
        selected = self.file_widget.selectedItems()
        # selection = pm.selected()

        # if only one selected and length of selection in scene is one
        # if len(selected) == 1 and len(selection) == 1:
        #     if selection[0].name() in selected[0].text():
        #         import_skin(selection[0], file_path=self.path_line.text()+selected[0].text())
        with pm.UndoChunk():
            for i in selected:
                obj_name = i.text().split('.sw')[0]

                # non unique name
                if '_-_' in obj_name:
                    obj_name = obj_name.replace('_-_', '|')
                # find obj in scene
                if not pm.ls(obj_name):
                    "=SKIN= Unable to find {} in scene.".format(obj_name)
                    continue

                import_skin(obj_name, file_path=self.path_line.text() + i.text())


class SkinToolMod(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SkinToolMod, self).__init__(parent)
        self.ui_name = 'SkinToolMod'
        self.ui_setting = ui_utils.ui_geom_setting(self, ui_name=self.ui_name, load=False, save=False)

        self.create_widget()
        self.create_connections()

        step_value = self.ui_setting.value('{}/spinBoxVal'.format(self.ui_name))
        if step_value:
            self.step_sb.setValue(float(step_value))
        self.restore_brush_value()

        self.apply_scl_tree_expand_status()
        self.modify_scl_influence_tree()

    def create_widget(self):
        main_lyt = QtWidgets.QHBoxLayout()
        self.setLayout(main_lyt)

        btn_grid = QtWidgets.QGridLayout()
        btn_grid.setSpacing(5)
        main_lyt.addLayout(btn_grid)

        for i, txt in enumerate([0.0, 0.1, 0.5, 0.9, 1.0]):
            btn = QtWidgets.QPushButton(str(txt))
            btn_grid.addWidget(btn, 0, i)
            btn.clicked.connect(partial(self._set_brush_value, txt))

        self.minus_btn = QtWidgets.QPushButton('--')
        btn_grid.addWidget(self.minus_btn, 1, 0, 1, 2)\

        self.step_sb = QtWidgets.QDoubleSpinBox()
        self.step_sb.setDecimals(4)
        self.step_sb.setValue(.025)
        self.step_sb.setRange(.0001, 1)
        self.step_sb.setSingleStep(.001)
        btn_grid.addWidget(self.step_sb, 1, 2)

        self.add_btn = QtWidgets.QPushButton('++')
        btn_grid.addWidget(self.add_btn, 1, 3, 1, 2)

    def create_connections(self):
        self.minus_btn.clicked.connect(self._brush_value_reduction)
        self.add_btn.clicked.connect(self._brush_value_increment)

        for item in pm.lsUI(type='radioButton'):
            # find radio button in artAttrSkin ui and with OperRadio name
            if 'artAttrSkin' in item.name() and 'OperRadio' in item.name():
                radio_obj = pm.toPySideControl(item.name())
                radio_obj.toggled.connect(self.change_brush_mode)
        pass

    @staticmethod
    def _get_brush_value():
        return pm.floatSliderGrp('artAttrValueSlider', query=True, value=True)

    def _set_brush_value(self, value):
        # edit value on the slider and run mel to make sure maya register it
        pm.floatSliderGrp('artAttrValueSlider', edit=True, value=value)
        mel.eval('artSkinSetSelectionValue {} false artAttrSkinPaintCtx artAttrSkin;'.format(value))
        self.save_brush_value()
        return

    def restore_brush_value(self):
        """
        setting brush strength based on previously set value
        :return:
        """
        for item in pm.lsUI(type='radioButton'):
            # find radio button in artAttrSkin ui and with OperRadio name
            if 'artAttrSkin' in item.name() and 'OperRadio' in item.name() and item.getSelect():
                key = '{}/brush_{}'.format(self.ui_name, item.getLabel())
                val = self.ui_setting.value(key)
                if not val:
                    continue
                self._set_brush_value(float(val))

    def save_brush_value(self):
        """
        saving ui value
        :return:
        """
        for item in pm.lsUI(type='radioButton'):
            # find radio button in artAttrSkin ui and with OperRadio name
            if 'artAttrSkin' in item.name() and 'OperRadio' in item.name() and item.getSelect():
                key = '{}/brush_{}'.format(self.ui_name, item.getLabel())
                self.ui_setting.setValue(key, str(self._get_brush_value()))
        key = '{}/spinBoxVal'.format(self.ui_name)
        self.ui_setting.setValue(key, str(self.step_sb.value()))

    def _brush_value_increment(self):
        step = self.step_sb.value()
        if pm.getModifiers() == 1:
            step *= .5
        current = self._get_brush_value()
        val = step + current
        self._set_brush_value(val if val < 1 else 1.0)

    def _brush_value_reduction(self):
        step = self.step_sb.value()
        if pm.getModifiers() == 1:
            step *= .5
        current = self._get_brush_value()
        val = current - step
        self._set_brush_value(val if val > 0 else 0.0)

    def change_brush_mode(self):
        radio_btn = self.sender()
        mode = radio_btn.isChecked()
        key = '{}/brush_{}'.format(self.ui_name, radio_btn.text())

        if radio_btn.text() not in ['Replace', 'Add', 'Scale', 'Smooth']:
            return

        if mode:
            val = self.ui_setting.value(key) if self.ui_setting.value(key) else 0
            self._set_brush_value(float(val))

        else:
            self.ui_setting.setValue(key, str(self._get_brush_value()))

    def modify_scl_influence_tree(self):
        # use objectTypeUI to find ui type with name
        pm.treeView('theSkinClusterInflList', e=1, ecc=self.get_scl_tree_expand_status)

    @staticmethod
    def get_scl_tree_expand_status(name, status):
        scl = get_skin_cluster(pm.selected()[0])
        infl_status = []
        # print(name, status)
        children = pm.treeView('theSkinClusterInflList', query=1, children=1)

        # if shift is holding, expand/ hide all its children
        if pm.getModifiers() == 1:
            sub_children = pm.treeView('theSkinClusterInflList', query=1, children=name)[1:]
            for sub_child in sub_children:
                pm.treeView('theSkinClusterInflList', edit=1, expandItem=(sub_child, status))

        for child in children:
            if name == child and not status:
                infl_status.append(child)
                continue
            if not pm.treeView('theSkinClusterInflList', query=1, isItemExpanded=child):
                infl_status.append(child)

        if "infl_expand_status" not in pm.listAttr(scl):
            scl.addAttr("infl_expand_status", dataType='string')
        scl.infl_expand_status.set('##'.join(infl_status), type='string')

    @staticmethod
    def apply_scl_tree_expand_status():
        scl = get_skin_cluster(pm.selected()[0])
        if "infl_expand_status" not in pm.listAttr(scl):
            return
        infl_status = scl.infl_expand_status.get()
        infl_list = infl_status.split('##')
        for infl in infl_list:
            if pm.treeView('theSkinClusterInflList', query=1, itemExists=infl):
                try:
                    pm.treeView('theSkinClusterInflList', edit=1, expandItem=[infl, 0])
                except:
                    print("Failed on ", infl)
        # pm.treeView('theSkinClusterInflList', expendItem=SCL_INFLUENCE_EXPAND_STATUS[scl])


def get_skin_window():
    """call ShapeTweaksDialog"""
    global dialog_skin_file
    try:
        dialog_skin_file.close()
        dialog_skin_file.deleteLater()
    except Exception as ew:
        a = ew

    dialog_skin_file = SkinDialog()
    return dialog_skin_file


def modify_skin_tool():
    """
    use cmds.evalDeferred() to run this
    :return:
    """
    global skin_tool_mod
    try:
        skin_tool_mod.close()
        skin_tool_mod.deleteLater()
    except (Exception,):
        pass

    # get column layout of paint skin weight tool
    for item in pm.lsUI(type='radioButton'):
        # find radio button in artAttrSkin ui and with OperRadio name
        if 'artAttrSkin' in item.name() and 'OperRadio' in item.name():
            row = item.parent()
            row_obj = omui.MQtUtil.findControl(row)
            row_qt_obj = wrapInstance(int(row_obj), QtWidgets.QVBoxLayout)
            row_qt_parent = row_qt_obj.parent()
            qt_layout = row_qt_parent.layout()

            # call mod skin tool
            skin_tool_mod = SkinToolMod()
            qt_layout.addWidget(skin_tool_mod)
            return skin_tool_mod
    else:
        # unable to find ui
        return