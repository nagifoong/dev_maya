import os

import pymel.all as pm

from ..data import color_data

current_user = os.environ.get('USERNAME')
custom_icon_path = "{}icons\\".format(os.path.abspath(__file__).split('shelves')[0])

DEFAULT_PY_ICON = 'pythonFamily.png'
DEFAULT_MEL_ICON = 'commandButton.png'


def clear_shelves():
    """
    delete useless shelves
    :return:
    """
    shelves = ['Subdives', 'PaintEffects', 'Arnold', 'FX_Caching', 'MASH', 'MotionGraphics', 'FX', 'Rendering',
               'TURTLE', "XGen"]

    for shelf in shelves:
        if pm.shelfLayout(shelf, q=1, ex=1):
            print 'delete shelf', shelf
            pm.deleteUI(shelf, layout=1)


class _Shelf(object):
    """
    Create custom shelf in maya

    - usage:
    from shelves import common
    reload(common)
    pm.evalDeferred('common')
    """

    def __init__(self, name='', icon_path='', parent='ShelfLayout'):
        self.name = name
        self.icon_path = icon_path
        self.parent = parent

        self.label_bg = (0, 0, 0, .5)
        self.label_color = (.9, .9, .9)

        self.size = 37

        self._clean_old_shelf()
        # pm.setParent(self.name)

    def add_bt(self, label='', icon='commandButton.png', command='', ann='', double_command='',
               mi=(), mip=0, no_popup=True):
        pm.setParent(self.name)
        if icon:
            icon = self.icon_path + icon
        bt = pm.shelfButton(width=self.size, height=self.size, image=icon, l=label, command=command, annotation=ann,
                            dcc=double_command, imageOverlayLabel=label, olb=self.label_bg, olc=self.label_color,
                            mip=mip, mi=mi, noDefaultPopup=no_popup)
        return bt

    def add_menu_item(self, parent, label='', command='', icon='', divider=False):
        if icon:
            icon = self.icon_path + icon
        if divider:
            return pm.menuItem(p=parent, divider=divider)
        return pm.menuItem(p=parent, l=label, c=command, i=icon)

    def add_sub_menu(self, parent, label='', icon=''):
        if icon:
            icon = self.icon_path + icon
        return pm.menuItem(p=parent, l=label, subMenu=1, i=icon)

    @staticmethod
    def add_separator():
        pm.separator(style='in', width=20, horizontal=False)

    def _clean_old_shelf(self):
        if pm.shelfLayout(self.name, ex=1):
            if pm.shelfLayout(self.name, q=1, ca=1):
                for item in pm.shelfLayout(self.name, q=1, ca=1):
                    pm.deleteUI(item)

        else:
            pm.shelfLayout(self.name, p=self.parent)

    def read(self):
        output = []
        temp = []
        for child in pm.shelfLayout(self.name, q=1, ca=1):
            if 'separator' in child:
                output.append(temp)
                temp = []
                continue
            temp.append(child)
        output.append(temp)
        print output
        return output


class ToolBeltShelf(_Shelf):
    def __init__(self, name='ToolBelt'):
        super(ToolBeltShelf, self).__init__(name=name)
        self.build()

    def build(self):
        self.add_bt(label='', ann='Reload Shelf', icon='refresh.png', no_popup=True,
                    command='from PyCharmScripts.shelves import shelf_toolbelt; reload(shelf_toolbelt); '
                            'shelf_toolBelt_var=shelf_toolbelt.ToolBeltShelf()')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'Get child array',
                           command='from PyCharmScripts.shelves import shelf_toolbelt; reload(shelf_toolbelt); '
                                   'shelf_toolBelt_var.read()')

        self.add_separator()
        # editors
        self.add_bt(label='EDI', ann='Editors', icon='menuIconWindow.png', no_popup=True)
        o = pm.popupMenu(b=1)
        self.add_menu_item(o, 'Node Editor', command='pm.mel.eval("NodeEditorWindow")')
        self.add_menu_item(o, 'Component Editor', command='pm.mel.eval("ComponentEditor")')
        self.add_menu_item(o, 'Connection Editor', command='pm.mel.eval("ConnectionEditor")')
        self.add_menu_item(o, 'Attribute Spreadsheet', command='pm.mel.eval("SpreadSheetEditor")')
        self.add_menu_item(o, 'Shape Editor', command='pm.mel.eval("ShapeEditor")')
        self.add_menu_item(o, divider=True)
        self.add_menu_item(o, 'Expression Editor', command='pm.mel.eval("ExpressionEditor")')
        self.add_menu_item(o, 'Graph Editor', command='pm.mel.eval("GraphEditor")')
        self.add_menu_item(o, divider=True)
        self.add_menu_item(o, 'UV Editor', command='pm.mel.eval("TextureViewWindow")')
        self.add_menu_item(o, 'Hypershade', command='pm.mel.eval("HypershadeWindow")')

        # toggles
        self.add_bt(label='Tgl', ann='Poly and Nurbs', icon='menuIconDisplay.png', no_popup=True)
        o = pm.popupMenu(b=1)
        self.add_menu_item(o, 'CVs', command='pm.mel.eval("ToggleCVs")')
        self.add_menu_item(o, 'Face Normal', command='pm.mel.eval("ToggleFaceNormalDisplay")')
        self.add_menu_item(o, 'Local Rotation Axis', command='pm.mel.eval("ToggleLocalRotationAxes")')

        self.add_bt(label='Sel', ann='Select Hierarchy', icon='menuIconSelect.png', no_popup=True)
        o = pm.popupMenu(b=1)
        self.add_menu_item(o, 'Select Hierarchy', command='pm.mel.eval("SelectHierarchy")')
        self.add_menu_item(o, 'Select Joints', command='pm.mel.eval("SelectAllJoints")')

        self.add_bt(label='FT', ann='Freeze Transform', icon='menuIconModify.png',
                    command='pm.mel.eval("FreezeTransformations")')
        self.add_bt(label='CP', ann='Center Pivot', icon='menuIconModify.png',
                    command='pm.mel.eval("CenterPivot")')
        self.add_bt(label='Hist', ann='Delete construction history', icon='menuIconEdit.png',
                    command='pm.mel.eval("DeleteHistory")')
        self.add_bt(label='', ann='Unlock attributes', icon=custom_icon_path + 'unlock_attribute.png',
                    command='from PyCharmScripts.utils import channels;reload(channels);'
                            'channels.cb_status(pm.selected(),all=1,v=1,lock=0,show=1)')
        self.add_separator()

        # joints & skinning
        self.add_bt(label='', ann='Create Joint', icon='kinJoint.png', no_popup=True,
                    command='pm.mel.eval("JointTool")', double_command='pm.mel.eval("JointToolOptions")')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'Reset joint orient',
                           command='[q.jo.set([0] * 3) for q in pm.selected()]')

        self.add_bt(label='Vis', ann='Show or Hide Joint. Click once for show, twice for hide',
                    icon='kinJoint.png', no_popup=True,
                    command='from PyCharmScripts.utils import joints; reload(joints); '
                            'joints.set_joint_vis(v=False, status=True)',
                    double_command='from PyCharmScripts.utils import joints; reload(joints); '
                                   'joints.set_joint_vis(v=True, status=True)')
        self.add_bt(label='Label', ann='Auto Set Joint Label', icon='kinJoint.png', no_popup=True,
                    command='from PyCharmScripts.utils import joints; reload(joints); joints.set_joint_label()')
        self.add_bt(label='ngSkin', ann='ngSkin Tool', icon='ngSkinToolsShelfIcon.png', no_popup=True,
                    command='from ngSkinTools.ui.mainwindow import MainWindow;MainWindow.open()')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'ngSkinTools2', command='import ngSkinTools2; ngSkinTools2.open_ui()')

        self.add_bt(label='', ann='Paint Skin Weight', icon='paintSkinWeights.png', no_popup=True,
                    command='pm.mel.eval("ArtPaintSkinWeightsToolOptions")')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'Bind Skin', command='from PyCharmScripts.utils import skinning; reload(skinning); '
                                                   'skinning.create_scl(pm.selected())')

        self.add_bt(label='', ann='Mirror Skin Weight', icon='mirrorSkinWeight.png', no_popup=True,
                    command='pm.mel.eval("MirrorSkinWeights")',
                    double_command='pm.mel.eval("MirrorSkinWeightsOptions")')

        self.add_bt(label='', ann='Copy Skin Weight', icon='copySkinWeight.png', no_popup=True,
                    command='pm.mel.eval("CopySkinWeights")',
                    double_command='pm.mel.eval("CopySkinWeightsOptions")')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'Copy to multiple object. [source, targets]',
                           command='from PyCharmScripts.utils import skinning;reload(skinning); '
                                   'skinning.copy_skin(pm.selected())')

        self.add_bt(label='', ann='Import and Export skin weight to file', icon=custom_icon_path + 'in_out.png',
                    no_popup=True, command='from PyCharmScripts.utils import skinning; reload(skinning); '
                                           'skinning.get_skin_window()')

        self.add_separator()

        # objects and other functions
        self.add_bt(label='', ann='Create Locator', icon='locator.png', no_popup=True,
                    command='pm.mel.eval("CreateLocator")')
        self.add_bt(label='', ann='Create Nurbs', icon='circle.png', no_popup=True,
                    command='from PyCharmScripts.tools.controllerShape import ui; reload(ui); ui.get_ui_window()')
        o = pm.popupMenu(b=0)
        sub_crv = self.add_sub_menu(o, label='Curve Shape')
        imp_cmd = 'from PyCharmScripts.tools.controllerShape import main; reload(main);'
        cmd = imp_cmd + 'main.create("{0}", name="{0}", groups=[])'
        for shp in ['circle', 'square', 'cube', 'sphere', 'cylinder', 'diamond']:
            self.add_menu_item(sub_crv, shp, command=cmd.format(shp))
        self.add_menu_item(o, divider=True)
        self.add_menu_item(o, 'Color Left ({})'.format(color_data.SIDE_COLOR['left']),
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), side="left")')
        self.add_menu_item(o, 'Color Right ({})'.format(color_data.SIDE_COLOR['right']),
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), side="right")')
        self.add_menu_item(o, 'Color Middle ({})'.format(color_data.SIDE_COLOR['middle']),
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), side="middle")')

        self.add_menu_item(o, divider=True)

        self.add_menu_item(o, 'Normal Display',
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), display_type="normal")')
        self.add_menu_item(o, 'Template Display',
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), display_type="template")')
        self.add_menu_item(o, 'Reference Display',
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), display_type="reference")')

        self.add_menu_item(o, divider=True)

        self.add_menu_item(o, 'Disable Override',
                           command='from PyCharmScripts.tools.controllerShape import colors; '
                                   'reload(colors); colors.override_shape(pm.selected(), disable=True)')

        self.add_menu_item(o, divider=True)
        self.add_menu_item(o, 'Add group as parent',
                           command='from PyCharmScripts.tools.controllerShape import main; '
                                   'reload(main); main.add_group(pm.selected(), "grp", "temp_grp")')
        self.add_menu_item(o, 'Swap Curve Shape',
                           command='from PyCharmScripts.tools.controllerShape import main; '
                                   'reload(main); main.swap_curve(pm.selected()[0], pm.selected()[1:])')

        self.add_bt(label='', ann='EP curve tool options', icon='curveEP.png', no_popup=True,
                    command='pm.mel.eval("EPCurveToolOptions")')
        self.add_bt(label='', ann='Rebuild curve options', icon='rebuildCurve.png', no_popup=True,
                    command='pm.mel.eval("RebuildCurveOptions")')

        self.add_bt(label='', ann='Move object to target', icon=custom_icon_path + 'relocation.png', no_popup=True,
                    command='pm.delete(pm.parentConstraint(),pm.scaleConstraint())')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'Point', command='pm.delete(pm.pointConstraint())')
        self.add_menu_item(o, 'Orient', command='pm.delete(pm.orientConstraint())')
        self.add_menu_item(o, 'Scale', command='pm.delete(pm.scaleConstraint())')

        self.add_bt(label='', ann='Duplicate last object and move to target(s)'
                    , icon=custom_icon_path + 'dul_move.png', no_popup=True,
                    command='from PyCharmScripts.utils import common; reload(common); '
                            'common.duplicate_and_move(pm.selected())',
                    double_command='from PyCharmScripts.utils import common; reload(common); '
                                   'common.duplicate_and_move(pm.selected(),groups=["offset", "driven"])')
        o = pm.popupMenu(b=0)
        import_cmd = 'from PyCharmScripts.utils import common; reload(common); '
        cmd = import_cmd + '[pm.{}Constraint(q, common.replace_name(q.name(), "ctrl", "joint")) for q in pm.selected()]'
        self.add_menu_item(o, 'ParentConst', command=cmd.format('parent'))
        self.add_menu_item(o, 'PointConst', command=cmd.format('point'))
        self.add_menu_item(o, 'OrientConst', command=cmd.format('orient'))
        self.add_menu_item(o, 'ScaleConst', command=cmd.format('scale'))

        self.add_menu_item(o, divider=True)

        cmd = '[q.attr(at+ax).connect(pm.ls(common.replace_name(q.name(), "ctrl", "joint"))[0].attr(at+ax)) ' \
              'for q in pm.selected() for at in "{}" for ax in "xyz"]'
        self.add_menu_item(o, 'Direct Connect (T and R)', command=cmd.format('tr'))
        self.add_menu_item(o, 'Direct Connect (S)', command=cmd.format('s'))
        self.add_menu_item(o, 'Direct Connect (manual)',
                           command='[pm.selected()[0].attr(at+ax).connect(pm.selected()[1].attr(at+ax)) '
                                   'for at in "trs" for ax in "xyz"]')

        self.add_bt(label='', ann='Create Rivet to selected vertices. PolyMesh only.',
                    icon=custom_icon_path + 'rivet.png', no_popup=True,
                    command='from PyCharmScripts.utils import rivet; reload(rivet); rivet.get_rivet_window()')

        self.add_bt(label='', ann='Renamer Window', icon=custom_icon_path + 'renamer.png', no_popup=True,
                    command='import PyCharmScripts.tools.renamer.main as rnm; reload(rnm); rnm.run()')
        o = pm.popupMenu(b=0)
        self.add_menu_item(o, 'Rename all shape', command='[q.rename("{}Shape".format(q.getParent())) '
                                                          'for q in pm.ls(shapes=1, ni=1) if q.name() != '
                                                          '"{}Shape".format(q.getParent())]')

        self.add_bt(label='', ann='Artisan paint attributes tool options', icon='artAttr.png', no_popup=True,
                    command='pm.mel.eval("ArtPaintAttrToolOptions")')

        self.add_separator()
        # last button always have weird offset

        # TODO: point on surface and point on mesh
