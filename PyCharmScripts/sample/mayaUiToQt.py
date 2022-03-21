import pymel.all as pm
import maya.mel as mel
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance


def get_maya_window():
    """get maya window pointer"""
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtWidgets.QMainWindow)


def convert_to_qt(maya_ui, object_type):
    """
    Given the name of a Maya UI element of any type, return the corresponding QT Type object.
    """
    ptr = omui.MQtUtil.findControl(maya_ui)
    if ptr is None:
        ptr = omui.MQtUtil.findLayout(maya_ui)
        if ptr is None:
            ptr = omui.MQtUtil.findMenuItem(maya_ui)
    if ptr is not None:
        return wrapInstance(long(ptr), object_type)
    else:
        print "Unable to convert."


class ExampleFrameUI(QtWidgets.QDialog):
    """
    """
    def __init__(self, parent=get_maya_window()):
        super(ExampleFrameUI, self).__init__(parent=parent)

        self.setWindowTitle('Sample UI')

        self.width = 270
        self.height = 450

        self.resize(self.width, self.height)

        self.create_widget()
        # self.create_connection()
        self.show()

    def create_widget(self):
        main_lyt = QtWidgets.QVBoxLayout()
        self.setLayout(main_lyt)

        maya_frame = pm.frameLayout('testFrame', cll=1, cl=0, l='Sample Frame')
        pm.columnLayout('testLayout', p=maya_frame)
        qt_frame = convert_to_qt(maya_frame, QtWidgets.QWidget)
        main_lyt.addWidget(qt_frame)
        qt_column = qt_frame.layout()

        lbl = QtWidgets.QLabel('This is a test QLable')
        qt_column.addWidget(lbl)

        bt = QtWidgets.QPushButton('This is a QPushButton')
        qt_column.addWidget(bt)

        mayb_frame = pm.frameLayout('testFrame', cll=1, cl=0, l='Sample Frame')
        pm.columnLayout('testLayout', p=mayb_frame)
        qt_frameb = convert_to_qt(mayb_frame, QtWidgets.QWidget)
        main_lyt.addWidget(qt_frameb)
        qt_columnb = qt_frameb.layout()

        lbl = QtWidgets.QLabel('This is a test QLable B')
        qt_columnb.addWidget(lbl)

        bt = QtWidgets.QPushButton('This is a QPushButton B')
        qt_columnb.addWidget(bt)



def run():
    """call main ui"""
    global dialog
    try:
        dialog.close()
        dialog.deleteLater()
    except Exception as ew:
        a = ew

    dialog = ExampleFrameUI()
    return dialog