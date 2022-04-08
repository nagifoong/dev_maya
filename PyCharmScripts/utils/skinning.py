import pickle
import os
import pymel.all as pm
import maya.mel as mel
from PySide2 import QtWidgets, QtGui

import ui_utils
from ..data import name_data

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
        return scl
    else:
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