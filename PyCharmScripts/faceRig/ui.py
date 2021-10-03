import pymel.all as pm
from PySide2 import QtWidgets, QtCore, QtGui
from ..utils import ui_utils

from functools import partial

reload(ui_utils)


class FaceRigUI(QtWidgets.QDialog):
    """
    Create lips rig ui
    """
    def __init__(self, parent=''):
        super(FaceRigUI, self).__init__(parent=parent)
        self.setWindowTitle('Create Face Rig')

        self.ui_name = 'FaceRigDialog'

        self.width = 400
        self.height = 620

        self.resize(self.width, self.height)
        # self.setFixedSize(self.size())

        self.create_widget()

        self.setStyleSheet("QGroupBox { border: .5px solid rgb(0, 0, 0); }")

        # to load ui position and size
        ui_utils.ui_geom_setting(self, ui_name=self.ui_name, load=True)
        self.show()

    def closeEvent(self, event):
        # to save ui position and size
        ui_utils.ui_geom_setting(self, ui_name=self.ui_name, save=True)
        QtWidgets.QDialog.closeEvent(self, event)

    def create_widget(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # scroll_layout = main_layout
        scroll_layout = QtWidgets.QVBoxLayout()
        scroll_layout.setContentsMargins(0, 5, 0, 0)
        def_widget = QtWidgets.QWidget()
        def_widget.setLayout(scroll_layout)

        def_scroll = QtWidgets.QScrollArea()
        def_scroll.setFixedWidth(350)
        def_scroll.setWidgetResizable(True)
        def_scroll.setWidget(def_widget)
        main_layout.addWidget(def_scroll)

        # eye rig
        eye_frame = ui_utils.FrameWidget(title='Eye Rig')
        # eye_frame.setFixedSize(350, 180)
        scroll_layout.addWidget(eye_frame)
        eye_lay = QtWidgets.QVBoxLayout()
        eye_lay.setSpacing(10)
        eye_frame.setLayout(eye_lay)
        for i in range(5):
            bt = QtWidgets.QPushButton(str(i))
            eye_lay.addWidget(bt)

        # lip rig
        lip_frame = ui_utils.FrameWidget(title='Lip Rig')
        # lip_frame.setFixedSize(350, 180)
        scroll_layout.addWidget(lip_frame)
        lip_lay = QtWidgets.QVBoxLayout()
        lip_lay.setSpacing(10)
        lip_frame.setLayout(lip_lay)

        loop_bt, self.loop_line = self.create_bt_line('Edge Loop', lip_lay, None)
        lip_gb = QtWidgets.QGroupBox('* Optional')
        lip_lay.addWidget(lip_gb)
        gb_lay = QtWidgets.QGridLayout()
        gb_lay.setSpacing(2)
        gb_lay.setContentsMargins(6, 15, 6, 6)
        lip_gb.setLayout(gb_lay)
        up_bt, self.up_line = self.create_bt_line('Up Vertex', gb_lay, 0)
        down_bt, self.down_line = self.create_bt_line('Lo Vertex', gb_lay, 1)
        side_bt, self.side_line = self.create_bt_line('Mouth Corner Vertices', gb_lay, 2)

        scroll_layout.addStretch(1)
        # build button
        build_bt = QtWidgets.QPushButton('Build Face Rig')
        main_layout.addWidget(build_bt)

    def create_bt_line(self, bt_text, parent, row):
        bt = QtWidgets.QPushButton(bt_text)
        line = QtWidgets.QLineEdit()
        line.setEnabled(False)
        bt.clicked.connect(partial(self.get_selection, line))

        if row is None:
            lay = QtWidgets.QHBoxLayout()
            parent.addLayout(lay)

            lay.addWidget(bt)
            lay.addWidget(line)
        else:
            parent.addWidget(bt, row, 0)
            parent.addWidget(line, row, 1)

        return bt, line

    @staticmethod
    def get_selection(line_edit):
        sel = pm.selected()
        line_edit.setText(','.join([s.name() for s in sel]))


def get_face_rig_dialog():
    """call controller shape library"""
    global face_rig_dialog
    try:
        face_rig_dialog.close()
        face_rig_dialog.deleteLater()
    except Exception as ew:
        a = ew

    face_rig_dialog = FaceRigUI(parent=ui_utils.get_maya_window())
    return face_rig_dialog