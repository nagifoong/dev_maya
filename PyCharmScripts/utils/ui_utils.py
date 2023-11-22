import os

import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance

dark_style = os.path.abspath(__file__).split('utils')[0] + 'data\\stylesheet.qss'


def eliminate_outliner_callback(client_data):
    """
    delete "Cant find procedure 'look' "
    :param client_data:
    :return:
    """
    all_panels = cmds.getPanel(type="outlinerPanel") or []
    for panel in all_panels:

        sc = cmds.outlinerEditor(panel, q=True, selectCommand=True)
        if sc is not None:  # if there are selectCommand set...

            print("KILL INFECTED outliner!!!")

            cmds.outlinerPanel(panel, e=True, unParent=True)  # remove infected panel
            cmds.file(uiConfiguration=False)  # mark as do not save ui info within scene file

            if (
                    cmds.optionVar(exists="useScenePanelConfig") and
                    cmds.optionVar(q="useScenePanelConfig") == 0
            ):
                mel.eval("$gOutlinerPanelNeedsInit = 1;")  # flag to restore later

    mel.eval("initOutlinerPanel();")  # restore outliner if flagged


def eliminate_model_panel_callback(*args):
    """
    remove call back
    :param args:
    :return:
    """

    EVIL_METHOD_NAMES = ['DCF_updateViewportList', 'CgAbBlastPanelOptChangeCallback']

    model_panel_label = mel.eval('localizedPanelLabel("ModelPanel")')
    processed = []

    panel_name = cmds.sceneUIReplacement(getNextPanel=('modelPanel', model_panel_label))
    while panel_name and panel_name not in processed:

        editor_changed_cb_text = cmds.modelEditor(panel_name, query=True, editorChanged=True)
        suspected_lines = editor_changed_cb_text.split(';')
        purified_lines = []
        changed = False

        for line in suspected_lines:
            for evil in EVIL_METHOD_NAMES:
                if evil.upper() in line.upper():
                    changed = True
                    break
            else:
                purified_lines.append(line)

        if changed:
            # logger.info("kill infected modelPanel %s", panel_name)
            cmds.modelEditor(panel_name, edit=True, editorChanged=';'.join(purified_lines))
            cmds.file(uiConfiguration=False)  # mark as do not save ui info within scene file

        processed.append(panel_name)
        panel_name = cmds.sceneUIReplacement(getNextPanel=('modelPanel', model_panel_label))


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


def set_stylesheet(win=None):
    """
    set stylesheet for win
    :param win:
    :return:
    """
    with open(dark_style, 'r') as ds:
        style = ds.read()
    win.setStyleSheet(style)

    return


def ui_geom_setting(wind, ui_name='defaultUI', company='nagi_dev', load=False, save=False):
    """save and load ui position and size"""
    setting = QtCore.QSettings(company, ui_name)
    key = '{}/geometry'.format(ui_name)
    if load:
        value = setting.value(key)
        if value:
            wind.restoreGeometry(value)

    elif save:
        setting.setValue(key, wind.saveGeometry())

    else:
        return setting


class QHLine(QtWidgets.QHBoxLayout):
    """
    add Horizontal line
    """
    def __init__(self, text=None):
        super(QHLine, self).__init__()

        if text:
            text = QtWidgets.QLabel(text)
            text.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
            self.addWidget(text)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.addWidget(line)


class FrameWidget(QtWidgets.QGroupBox):
    def __init__(self, title='', parent=None):
        super(FrameWidget, self).__init__(title, parent)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(0)
        super(FrameWidget, self).setLayout(layout)

        self.__widget = QtWidgets.QFrame(parent)
        self.__widget.setFrameShape(QtWidgets.QFrame.Panel)
        self.__widget.setFrameShadow(QtWidgets.QFrame.Raised)
        self.__widget.setLineWidth(2)
        # self.__widget.setStyleSheet("QFrame {border: 2px solid black;}")
        layout.addWidget(self.__widget)

        self.__collapsed = False

    def setLayout(self, layout):
        self.__widget.setLayout(layout)

    def expandCollapseRect(self):
        return QtCore.QRect(0, 0, self.width(), 20)

    def mouseReleaseEvent(self, event):
        if self.expandCollapseRect().contains(event.pos()):
            self.toggleCollapsed()
            event.accept()
        else:
            event.ignore()

    def toggleCollapsed(self):
        self.setCollapsed(not self.__collapsed)

    def setCollapsed(self, state=True):
        self.__collapsed = state

        if state:
            self.setMinimumHeight(20)
            self.setMaximumHeight(20)
            self.__widget.setVisible(False)
        else:
            self.setMinimumHeight(0)
            self.setMaximumHeight(1000000)
            self.__widget.setVisible(True)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)

        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width()
        offset = 25

        painter.setRenderHint(painter.Antialiasing)
        painter.fillRect(self.expandCollapseRect(), QtGui.QColor(93, 93, 93))
        painter.drawText(
            x + offset, y + 3, w, 16,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop,
            self.title()
        )
        self.__draw_triangle(painter, x, y)  # (1)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.end()

    def __draw_triangle(self, painter, x, y):  # (2)
        if not self.__collapsed:  # (3)
            points = [QtCore.QPoint(x + 10, y + 6),
                      QtCore.QPoint(x + 20, y + 6),
                      QtCore.QPoint(x + 15, y + 11)
                      ]

        else:
            points = [QtCore.QPoint(x + 10, y + 4),
                      QtCore.QPoint(x + 15, y + 9),
                      QtCore.QPoint(x + 10, y + 14)
                      ]

        current_brush = painter.brush()  # (4)
        current_pen = painter.pen()

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(187, 187, 187),
                QtCore.Qt.SolidPattern
            )
        )  # (5)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))  # (6)
        painter.drawPolygon(QtGui.QPolygon(points))  # (7)
        painter.setBrush(current_brush)  # (8)
        painter.setPen(current_pen)
