import os

from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
import pymel.all as pm

# make sure use cmds.evalDeferred to load and unload custom ui/ shelves


class JointRadiusSlider(QtWidgets.QWidgetAction):
    def __init__(self, parent=''):
        """
        add a slider as a right click action to control joint radius
        :param parent:
        """
        super(JointRadiusSlider, self).__init__(parent)
        self.default_value = cmds.jointDisplayScale(query=True)
        self.create_widget()
        self.create_connection()
        self.spin_box.setValue(self.default_value)

    def create_widget(self):
        main_widget = QtWidgets.QWidget()
        self.setDefaultWidget(main_widget)

        main_layout = QtWidgets.QHBoxLayout()
        main_widget.setLayout(main_layout)

        lbl = QtWidgets.QLabel('radius:')
        main_layout.addWidget(lbl)

        self.spin_box = QtWidgets.QDoubleSpinBox()
        self.spin_box.setRange(.01, 10)
        self.spin_box.setSingleStep(.1)
        main_layout.addWidget(self.spin_box)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setRange(.1, 100)
        main_layout.addWidget(self.slider, 2)
        self.slider.installEventFilter(self)

    def create_connection(self):
        self.slider.sliderMoved.connect(self._update_spin_box_value)
        self.spin_box.valueChanged.connect(self._update_slider_value)
        self.spin_box.valueChanged.connect(self._update_joint_radius)

    def _update_slider_value(self):
        # make dynamic when 0.1 make step to 0.01
        old_val = self.slider.value()
        new_val = self.spin_box.value() * 10.0
        # print(old_val, new_val)
        if 2.0 <= old_val < new_val:
            self.spin_box.setSingleStep(.1)
        elif new_val < 2.0:
            self.spin_box.setSingleStep(0.01)
        self.slider.setValue(int(self.spin_box.value() * 10.0))

    def _update_spin_box_value(self):
        self.spin_box.setValue(self.slider.value() / 10.0)

    def _update_joint_radius(self):
        cmds.jointDisplayScale(self.spin_box.value())
