import pymel.all as pm
import maya.mel as mel
from PySide2 import QtWidgets, QtCore, QtGui

import colors
import main
from PyCharmScripts.data import color_data, name_data
from PyCharmScripts.utils import ui_utils

reload(main)
reload(colors)
reload(ui_utils)

import os
from functools import partial

folder_path = os.path.abspath(__file__).split('ui.py')[0]
thumbnail_path = folder_path + "thumbnails\\"

ALL_CONS = main.read_prefab().keys()


def get_thumbnail(name):
    """
    get thumbnail for shape
    :param name:
    :return:
    """
    file_name = '{}.1.png'.format(name)
    img_dir = pm.util.path(thumbnail_path)
    if img_dir.files(file_name):
        img_path = img_dir.files(file_name)[0]
    else:
        file_name = 'noThumbnail.1.png'
        if img_dir.files(file_name):
            img_path = img_dir.files(file_name)[0]

    return img_path


class ControllerUI(QtWidgets.QDialog):
    """
    UI that combine ControllerShape and ShapeTweaksDialog
    """
    def __init__(self, parent=''):
        super(ControllerUI, self).__init__(parent=parent)
        self.setWindowTitle('Create Controller')

        self.ui_name = 'controlShapeUI'

        self.width = 400
        self.height = 620

        self.resize(self.width, self.height)
        self.setFixedWidth(self.width)
        # self.setFixedHeight(self.height)
        # self.setFixedSize(self.size())

        self.create_widget()
        self.create_connections()
        self.setStyleSheet("QGroupBox { border: .5px solid rgb(0, 0, 0); }")

        # to load ui position and size
        ui_utils.ui_geom_setting(self, ui_name=self.ui_name, load=True)
        self.show()

    def create_widget(self):
        main_layout = QtWidgets.QGridLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(5, 0, 5, 5)
        self.setLayout(main_layout)

        # menu bar
        main_menu = QtWidgets.QMenuBar()
        menu = QtWidgets.QMenu(self)
        menu.setTitle('Options')

        self.add_lib = QtWidgets.QAction('Add to Library', self)
        menu.addAction(self.add_lib)
        menu.addSeparator()
        self.swap_crv = QtWidgets.QAction('Swap Curve', self)
        menu.addAction(self.swap_crv)
        menu.addSeparator()
        self.fix_width_action = QtWidgets.QAction('Fixed Width', self, checkable=True, checked=True)
        menu.addAction(self.fix_width_action)
        self.fix_height_action = QtWidgets.QAction('Fixed Height', self, checkable=True, checked=True)
        menu.addAction(self.fix_height_action)

        main_menu.addMenu(menu)
        main_layout.addWidget(main_menu, 0, 0, 1, 0)

        # shape library
        shp_gb = QtWidgets.QGroupBox('Nurbs')
        main_layout.addWidget(shp_gb, 1, 0, 1, 0)

        shp_layout = QtWidgets.QVBoxLayout()
        shp_gb.setLayout(shp_layout)
        self.shp_ui = ControllerShape(parent=None)
        shp_layout.addWidget(self.shp_ui)

        # color ui
        color_gb = QtWidgets.QGroupBox('Shape Tweaks')
        main_layout.addWidget(color_gb, 2, 0)
        clr_layout = QtWidgets.QVBoxLayout()
        color_gb.setLayout(clr_layout)
        clr_layout.addWidget(ShapeTweaksDialog(parent=None))
        return

    def closeEvent(self, event):
        # to save ui position and size
        ui_utils.ui_geom_setting(self, ui_name=self.ui_name, save=True)
        QtWidgets.QDialog.closeEvent(self, event)

    def create_connections(self):
        self.add_lib.triggered.connect(self.append_lib)
        self.swap_crv.triggered.connect(self.swap_crv_func)

    def append_lib(self):
        main.append_prefab(pm.selected()[0])
        self.shp_ui._update_list(main.read_prefab().keys())

    @staticmethod
    def swap_crv_func():
        sel = pm.selected()
        main.swap_curve(sel[0], sel[1:])

class ControllerShape(QtWidgets.QDialog):
    """
    controller shape library
    """
    def __init__(self, parent=''):
        super(ControllerShape, self).__init__(parent=parent)

        self.setWindowTitle('Create Controller')

        self.width = 270
        self.height = 450

        self.resize(self.width, self.height)

        self.create_widget()
        self.create_connection()
        self._update_list(ALL_CONS)
        ui_utils.set_stylesheet(win=self)
        self.show()

    def create_widget(self):
        gd_layout = QtWidgets.QGridLayout()
        gd_layout.setSpacing(4)
        self.setLayout(gd_layout)

        main_layout = QtWidgets.QVBoxLayout()
        # self.setLayout(main_layout)
        gd_layout.addLayout(main_layout, 0, 0)

        grp_layout = QtWidgets.QHBoxLayout()
        self.grp_check_box = QtWidgets.QCheckBox('Add Group(s):\t')
        self.grp_check_box.setChecked(True)
        self.grp_line_edit = QtWidgets.QLineEdit('nul')
        grp_layout.addWidget(self.grp_check_box)
        grp_layout.addWidget(self.grp_line_edit)
        main_layout.addLayout(grp_layout)

        self.default_name_radio = QtWidgets.QRadioButton('Default naming')
        main_layout.addWidget(self.default_name_radio)
        self.default_name_radio.setChecked(True)

        radio_layout = QtWidgets.QHBoxLayout()
        self.replace_name_radio = QtWidgets.QRadioButton('Replace string:')
        self.replace_name_edit = QtWidgets.QLineEdit('{},{}'.format(name_data.TYPE_LIST['joint'],
                                                                    name_data.TYPE_LIST['ctrl']))
        self.replace_name_edit.setEnabled(False)
        radio_layout.addWidget(self.replace_name_radio)
        radio_layout.addWidget(self.replace_name_edit)
        main_layout.addLayout(radio_layout)

        filter_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('Filter:')
        self.filter_line_edit = QtWidgets.QLineEdit()
        filter_layout.addWidget(label)
        filter_layout.addWidget(self.filter_line_edit)
        gd_layout.addLayout(filter_layout, 1, 0, 1, 2)

        self.shape_list = QtWidgets.QListWidget()
        self.shape_list.setMovement(QtWidgets.QListView.Static)
        gd_layout.addWidget(self.shape_list, 2, 0, 1, 2)

        txt_gb = QtWidgets.QGroupBox('Nurbs Text')
        gd_layout.addWidget(txt_gb, 0, 1)

        txt_main_layout = QtWidgets.QVBoxLayout()
        txt_gb.setLayout(txt_main_layout)
        txt_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('Text:')
        self.text_line_edit = QtWidgets.QLineEdit('Default')
        txt_layout.addWidget(label)
        txt_layout.addWidget(self.text_line_edit)
        txt_main_layout.addLayout(txt_layout)

        self.txt_create_bt = QtWidgets.QPushButton('Create')
        txt_main_layout.addWidget(self.txt_create_bt)

    def create_connection(self):
        self.grp_check_box.toggled.connect(self.grp_line_edit.setEnabled)
        self.replace_name_radio.toggled.connect(self.replace_name_edit.setEnabled)

        self.filter_line_edit.textChanged.connect(self._filter_changed)

        self.shape_list.itemDoubleClicked.connect(self.create_con)

        self.txt_create_bt.clicked.connect(self.create_text)

    def _filter_changed(self):
        """refresh list widget with filter"""
        filter_text = self.filter_line_edit.text()

        updated = []
        for con in ALL_CONS:
            if filter_text.lower() in con.lower():
                updated.append(con)

        self._update_list(updated)

    def _update_list(self, updated_list):
        """update list widget"""
        self.shape_list.clear()

        self.shape_list.setViewMode(QtWidgets.QListWidget.IconMode)
        shape_size = 65
        buffer_size = 12
        self.shape_list.setIconSize(QtCore.QSize(shape_size, shape_size))
        self.shape_list.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.shape_list.setGridSize(QtCore.QSize(shape_size + buffer_size, shape_size + buffer_size))

        for obj in sorted(updated_list):
            img = get_thumbnail(obj)
            item = QtWidgets.QListWidgetItem(obj)
            item.setIcon(QtGui.QIcon(img))
            self.shape_list.addItem(item)

    def create_con(self):
        """create controller when list widget item is double clicked"""
        con = self.shape_list.currentItem().text()
        grps = []
        name = con
        new_cons = []
        if self.grp_check_box.isChecked():
            grps = self.grp_line_edit.text().split(',')
        pm.undoInfo(openChunk=True)
        if pm.selected():
            for obj in pm.selected():
                name = obj
                if not self.default_name_radio.isChecked():
                    key = self.replace_name_edit.text().split(',')
                    if key[0] not in name.name():
                        name = "{}_{}".format(name, key[1])
                    else:
                        name = name.replace(key[0], key[1])
                con_struc = main.create(con, name=name, groups=grps)
                pm.matchTransform(con_struc[0], obj)
                new_cons.append(con_struc)
        else:
            con_struc = main.create(con, name=name, groups=grps)
            new_cons.append(con_struc)
        pm.undoInfo(closeChunk=True)
        return new_cons

    def create_text(self):
        """create nurbs curve based on text"""
        name = self.text_line_edit.text()
        if self.grp_check_box.isChecked():
            grps = self.grp_line_edit.text().split(',')
        con_struc = main.create(None, name=name, text=name, groups=grps)
        return con_struc


class ShapeTweaksDialog(QtWidgets.QDialog):
    """ui with all usable color in maya"""
    def __init__(self, parent=None):
        # self.delete_instance()
        # self.__class__.ui_instance = self
        super(ShapeTweaksDialog, self).__init__(parent)

        self.setWindowTitle('Color Shapes')

        self.width = 270
        self.height = 137
        self.resize(self.width, self.height)

        self.create_widget()
        self.show()

    def create_widget(self):
        main_layout = QtWidgets.QVBoxLayout()
        # main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # shape rotate
        main_layout.addWidget(QtWidgets.QLabel('Shape Rotate:'))
        rot_layout = QtWidgets.QGridLayout()
        rot_layout.setVerticalSpacing(4)
        rot_layout.setHorizontalSpacing(2)
        main_layout.addLayout(rot_layout)

        rot_layout.addWidget(QtWidgets.QLabel('Multiplier:'), 0, 0)
        rot_mult_spin = QtWidgets.QSpinBox()
        self.rot_spin_box = rot_mult_spin
        rot_mult_spin.setValue(45)
        rot_mult_spin.setSingleStep(15)
        rot_mult_spin.setMinimum(15)
        rot_mult_spin.setMaximum(180)

        rot_layout.addWidget(rot_mult_spin, 0, 1)
        rot_i = 0
        for ax in 'xyz':
            for m in '+-':
                bt = QtWidgets.QPushButton(m + ' ' + ax)
                bt.clicked.connect(self.rotate_shape)
                rot_layout.addWidget(bt, 1, rot_i)
                rot_i += 1

        # shape size
        main_layout.addWidget(QtWidgets.QLabel('Shape Scale:'))
        size_layout = QtWidgets.QHBoxLayout()
        size_layout.setSpacing(2)
        main_layout.addLayout(size_layout)

        for ty in [-1, .9, 1.1, 2]:
            bt = QtWidgets.QPushButton('x {}'.format(ty))
            bt.clicked.connect(partial(self.set_size, ty))
            size_layout.addWidget(bt)

        # main_layout.addLayout(ui_utils.QHLine('Color'), 0, 0)
        main_layout.addLayout(ui_utils.QHLine('Color'))
        color_layout = QtWidgets.QGridLayout()
        color_layout.setSpacing(0)
        main_layout.addLayout(color_layout)

        row = 0
        column = 0

        # define how many item per row
        column_max = 4

        # sort color list, make blue, yellow and red always at the top
        color_list = sorted(color_data.COLOR_DICT.values())
        color_list.remove(6)
        color_list.remove(13)
        color_list.remove(17)
        main_list = [6, 17, 13]

        # create buttons
        for color in main_list:
            bt = QtWidgets.QPushButton()
            if color in color_data.QT_DICT.keys():
                r, g, b = color_data.QT_DICT[color]
                bt.setStyleSheet('background-color:rgb({},{},{})'.format(r, g, b))
            
                bt.setText(str(color))
            bt.clicked.connect(partial(self.set_shape, color, None))

            color_layout.addWidget(bt, row, column)

            column += 1
            if column > (column_max - 1):
                row += 1
                column = 0

        # button to disable color of the shapes
        bt = QtWidgets.QPushButton("No Color")
        color_layout.addWidget(bt, row, column)
        bt.clicked.connect(partial(self.set_shape, 'disable', None))

        # a line with buttons for secondary colors
        sec_color_lay = QtWidgets.QHBoxLayout()
        color_layout.addLayout(sec_color_lay, 2, 0, 1, 4)
        for color in color_list:
            bt = QtWidgets.QPushButton()
            if color in color_data.QT_DICT.keys():
                r, g, b = color_data.QT_DICT[color]
                bt.setStyleSheet('background-color:rgb({},{},{})'.format(r, g, b))

                bt.setText(str(color))
            bt.clicked.connect(partial(self.set_shape, color, None))
            sec_color_lay.addWidget(bt)

        # display type
        main_layout.addLayout(ui_utils.QHLine('Display Type'))

        type_layout = QtWidgets.QGridLayout()
        type_layout.setSpacing(2)
        main_layout.addLayout(type_layout)

        for i, ty in enumerate(['normal', 'template', 'reference']):
            bt = QtWidgets.QPushButton(ty)
            type_layout.addWidget(bt, 0, i)
            bt.clicked.connect(partial(self.set_shape, None, ty))

    @staticmethod
    def set_shape(color, display_type):
        if color:
            if color == 'disable':
                colors.override_shape(pm.selected(), disable=True)
            else:
                colors.override_shape(pm.selected(), color=color)
            print color
        if display_type:
            colors.override_shape(pm.selected(), display_type=display_type)

    @staticmethod
    def set_size(value):
        with pm.UndoChunk():
            ori_sel = pm.selected()
            if len(ori_sel) == 0:
                print '--No curve is selected.--'
                return
            mel.eval('selectCurveCV("all");')
            pm.scale(value, value, value, a=1)
            pm.select(ori_sel)

    def rotate_shape(self):
        with pm.UndoChunk():
            ori_sel = pm.selected()
            direction = self.sender().text()
            multiplier = self.rot_spin_box.value() if "+" in direction else self.rot_spin_box.value() * -1
            mel.eval('selectCurveCV("all");')
            if 'z' in direction:
                pm.rotate(multiplier, 0, 0, os=1, a=1)
            elif 'x' in direction:
                pm.rotate(0, multiplier, 0, os=1, a=1)
            else:
                pm.rotate(0, 0, multiplier, os=1, a=1)
            pm.select(ori_sel)


def get_color_window():
    """call ShapeTweaksDialog"""
    global dialog_color
    try:
        dialog_color.close()
        dialog_color.deleteLater()
    except Exception as ew:
        a = ew

    dialog = ShapeTweaksDialog(parent=ui_utils.get_maya_window())
    return dialog


def get_ui_window():
    """call main ui"""
    global dialog
    try:
        dialog.close()
        dialog.deleteLater()
    except Exception as ew:
        a = ew

    dialog = ControllerUI(parent=ui_utils.get_maya_window())
    return dialog


def get_shape_window():
    """call controller shape library"""
    global dialog_shp
    try:
        dialog_shp.close()
        dialog_shp.deleteLater()
    except Exception as ew:
        a = ew

    dialog = ControllerShape(parent=ui_utils.get_maya_window())
    return dialog


if __name__ == "__main__":
    get_ui_window()
