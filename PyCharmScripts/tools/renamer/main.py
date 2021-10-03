import maya.cmds as cmds
from functools import partial


class Renamer:
    def __init__(self):
        self.sj = None
        self._run()
        pass

    @staticmethod
    def replace_string(n):
        a = n.split("|")
        return a[-1]

    def set_prefix_suffix(self, n):
        preT = cmds.textFieldGrp('tfPrefix', q=1, tx=1)
        sufT = cmds.textFieldGrp('tfSuffix', q=1, tx=1)

        nameFields = cmds.scrollLayout('scrollRF', q=1, ca=1)
        for q in range(len(nameFields)):
            nameFields[q] = cmds.nameField(nameFields[q], q=1, fpn=0, o=1)
            newName = preT + self.replace_string(nameFields[q]) + sufT
            cmds.rename(nameFields[q], newName)

        cmds.textFieldGrp('tfPrefix', e=1, tx="")
        cmds.textFieldGrp('tfSuffix', e=1, tx="")

    def find_and_replace(self, n):
        seName = cmds.textFieldGrp('tfSearch', q=1, tx=1)
        reName = cmds.textFieldGrp('tfReplace', q=1, tx=1)
        nameFields = cmds.scrollLayout('scrollRF', q=1, ca=1)
        for q in range(len(nameFields)):
            nameFields[q] = cmds.nameField(nameFields[q], q=1, fpn=0, o=1)
            temp = nameFields[q].replace(seName.replace(" ", "_"), reName)
            cmds.rename(nameFields[q], self.replace_string(temp))

        cmds.textFieldGrp('tfSearch', e=1, tx="")
        cmds.textFieldGrp('tfReplace', e=1, tx="")

    def name_with_increment(self, n):
        inPre = cmds.textFieldGrp('tfIncreName', q=1, tx=1)
        inNo = cmds.textFieldGrp('tfIncreNum', q=1, tx=1)
        try:
            int_no = int(inNo)
        except:
            cmds.warning('Increment digit error.')
            return
        nameFields = cmds.scrollLayout('scrollRF', q=1, ca=1)
        user_padding = len(inNo)
        padding = len(str(len(nameFields)))
        padding = user_padding if user_padding > padding else padding
        for q in range(len(nameFields)):
            nameFields[q] = cmds.nameField(nameFields[q], q=1, o=1)
            cmds.rename(nameFields[q], inPre + str(q + int_no).zfill(padding))

    def refresh_content(self, n, hi=False):
        """
        update name fields
        :param n:
        :param hi:
        :return:
        """
        if hi:
            cmds.select(hi=1)

        selection = cmds.ls(sl=True)

        if cmds.scrollLayout('scrollRF', q=1, ca=1):
            for q in cmds.scrollLayout('scrollRF', q=1, ca=1):
                cmds.deleteUI(q)

        if cmds.menuItem("shpVisCb", q=1, cb=1) == 1:
            for sel in selection:
                if sel not in cmds.ls(s=1):
                    cmds.nameField(o=sel, p='scrollRF')
        else:
            for sel in selection:
                cmds.nameField(o=sel, p='scrollRF')

    # def kill_script(self):
    #     """
    #     clean up
    #     :return:
    #     """
    #     if self.sj:
    #         cmds.scriptJob(k=self.sj)
    #         self.sj = None
    #     # for script in cmds.scriptJob(lj=1):
    #     #     if "renewNF(" in script:
    #     #         cmds.scriptJob(k=int(script.split(":")[0]))

    def refresh_ui(self):
        self.sj = cmds.scriptJob(e=['SelectionChanged', partial(self.refresh_content, 0)])
        cmds.scriptJob(uid=['windowRnm', partial(cmds.scriptJob, k=self.sj)])
        print self.sj

    def _run(self):
        # if cmds.window('windowRnm', q=1, ex=1):
        #     cmds.deleteUI('windowRnm')
        window = cmds.window('windowRnm', t='Renamer', wh=(231, 636), vis=1, mb=1)
        cmds.menu("viewMenu", l="Show", p='windowRnm')
        cmds.menuItem("shpVisCb", cb=1, p='viewMenu', l="Hide Shapes", c=self.refresh_content)
        # cmds.window('windowRnm',q=1,wh=1)
        # cmds.columnLayout(adj=1,w=200,cal="left")##
        cmds.formLayout('mainF', nd=100)
        cmds.scrollLayout('scrollRF', cr=1, p='mainF')  #
        self.refresh_content(False)

        cmds.frameLayout('frameIncre', l="Increment Rename", bv=1, cll=0, p='mainF')
        cmds.columnLayout('colIncre', adj=1, w=200, cal="left", p='frameIncre')
        cmds.textFieldGrp('tfIncreName', p='colIncre', adj=2, l="Name:", cl2=["left", "left"], cw2=[60, 130])
        cmds.textFieldGrp('tfIncreNum', p='colIncre', adj=2, l="Start From:", cl2=["left", "left"], cw2=[60, 130], tx=1)
        cmds.button('btIncre', p='colIncre', l="Apply", w=80, c=self.name_with_increment)

        cmds.frameLayout('framePreSuf', l="Prefix/Suffix", bv=1, cll=0, p='mainF')
        cmds.columnLayout('colPreSuf', adj=1, w=200, cal="left", p='framePreSuf')
        cmds.textFieldGrp('tfPrefix', p='colPreSuf', adj=2, l="Prefix:", cl2=["left", "left"], cw2=[60, 130])
        cmds.textFieldGrp('tfSuffix', p='colPreSuf', adj=2, l="Suffix:", cl2=["left", "left"], cw2=[60, 130])
        cmds.button('btPreSuf', p='colPreSuf', l="Apply", w=80, c=self.set_prefix_suffix)

        cmds.frameLayout('frameSeRe', l="Search&Replace", bv=1, cll=0, p='mainF')  ##
        cmds.columnLayout('colSeRe', adj=1, w=200, cal="left", p='frameSeRe')  #
        cmds.textFieldGrp('tfSearch', adj=2, l="Search:", cl2=["left", "left"], cw2=[60, 130], p='colSeRe')
        cmds.textFieldGrp('tfReplace', adj=2, l="Replace:", cl2=["left", "left"], cw2=[60, 130], p='colSeRe')
        cmds.button('btSeRe', l="Apply", w=80, c=self.find_and_replace, p='colSeRe')
        cmds.rowLayout('rowBtLayout', ad2=2, nc=2, p='mainF')
        cmds.button("btRE", l="Refresh Selection", h=35, w=100, c=self.refresh_content, p='rowBtLayout')
        cmds.button("btHI", l="Refresh Selection \n with Hierarchy", h=35, w=100,
                    c=partial(self.refresh_content, hi=1), p='rowBtLayout')
        cmds.button('btClose', l="Close", h=30, w=100, c="cmds.deleteUI('windowRnm')", p='mainF')

        cmds.formLayout('mainF', e=1, ac=[('frameIncre', 'top', 5, 'scrollRF'), ('framePreSuf', 'top', 5, 'frameIncre'),
                                          ('frameSeRe', 'top', 5, 'framePreSuf'), ("rowBtLayout", 'top', 5, 'frameSeRe'),
                                          ("btClose", 'top', 5, "rowBtLayout")],
                        af=[('scrollRF', 'left', 5), ('scrollRF', 'right', 5), ('scrollRF', 'top', 5),
                            ('scrollRF', 'bottom', 370),
                            ('framePreSuf', 'left', 5), ('framePreSuf', 'right', 5),
                            ('frameIncre', 'left', 5), ('frameIncre', 'right', 5),
                            ('frameSeRe', 'left', 5), ('frameSeRe', 'right', 5),
                            ("rowBtLayout", 'left', 5), ("rowBtLayout", 'right', 5),
                            ("btClose", 'left', 5), ("btClose", 'right', 5)])
        self.refresh_ui()


def run():
    if cmds.window('windowRnm', q=1, ex=1):
        cmds.deleteUI('windowRnm')
    Renamer()
