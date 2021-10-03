import pymel.all as pm

shelfLabel = ['Windows', 'Objects and Transforms', 'Joints and Skinning', 'Tools', 'Third party']
workSpaceName = 'Custom Shelf'
custShelfPath = "{}/{}".format("/".join(pm.about(env=1).split("/")[:-1]), 'prefs/shelves/shelf_Custom.mel')


def run():
    """Delete before create workspace control"""
    if pm.workspaceControl("dulpCustomWorkspaceControl", q=1, ex=1):
        pm.workspaceControl("dulpCustomWorkspaceControl", e=1, cl=1)

    wp = pm.workspaceControl("dulpCustomWorkspaceControl", ih=112, l=workSpaceName, retain=False,
                             floating=True, uiScript="from PyCharmScripts.utils import duplicateShelf;"
                                                     "reload(duplicateShelf); duplicateShelf.createFromFile()")
    return


def createFromFile():
    cusShelves = []
    '''Skip if custom_shelf.mel does not exist'''
    if not pm.util.path(custShelfPath).exists():
        return

    '''Open and rend the file'''
    with open(custShelfPath) as f:
        line = f.read()

    '''Split with shelf button and separator'''
    btns = ";".join(line.split(";")[3:])[:-4].split("\n    shelfButton")
    ite = 1
    nbt = ''

    '''Main layout'''
    mainCol = pm.columnLayout(adj=1)

    '''First frame layout'''
    cusShelf = pm.frameLayout('dulpCustomShelf{}'.format(ite), label=shelfLabel[ite-1], p=mainCol, cll=1)
    gdLay = pm.gridLayout('dulpCustGL{}'.format(ite), nc=8, cwh=(35, 35), p=cusShelf)

    '''Create button and subsequent frame layouts'''
    for bt in btns[1:]:
        nbt = nbt + ';shelfButton -parent "dulpCustGL{}" {}'.format(ite,bt.split(';\n    separator\n')[0])
        if ';\n    separator\n' in bt:
            # nbt = nbt +  ';shelfButton -parent "dulpCustGL{}" {}'.format(ite, bt.split(';\n    separator\n')[0])
            ite += 1
            pm.mel.eval(nbt)
            pm.frameLayout(cusShelf, e=1, cl=1)
            cusShelf = pm.frameLayout('dulpCustomShelf{}'.format(ite), label=shelfLabel[ite-1], p=mainCol, cll=1)
            gdLay = pm.gridLayout('dulpCustGL{}'.format(ite), nc=8, cwh=(35, 35), p=cusShelf)
            nbt=''
        # finalLine = finalLine + nbt
    '''Action for last frame layout'''
    pm.mel.eval(nbt)
    pm.frameLayout(cusShelf, e=1, cl=1)


if __name__ == '__main__':
    run()