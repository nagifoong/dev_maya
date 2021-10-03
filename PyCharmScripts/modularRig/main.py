import pymel.all as pm

from . import utils

create_name = utils.create_name


class Base:
    def __init__(self, side='m', name='default'):
        self.side = side
        self.name = name
        self.main_node = pm.group(name=create_name(side=side, name=name, type='group'), em=1)

        # add side and cmpt_name attribute
        self.main_node.addAttr('side', dt='string')
        self.main_node.side.set(side, type='string', l=1)
        self.main_node.addAttr('cmpt_name', dt='string')
        self.main_node.cmpt_name.set(name, type='string', l=1)

        # create basic structure for the component
        for at_name in ['deform', 'rig', 'guide', 'noTouch']:
            grp = pm.group(name=create_name(side=side, name='{}_{}'.format(name, at_name), type='group'), em=1,
                           p=self.main_node)
            # create attribute on main node and connect message attribute to it
            self.main_node.addAttr(at_name, at='message')
            grp.message.connect(self.main_node.attr(at_name))

            # if at_name is guide,
            # create "guide_node" to store nodes which needed to be deleted after rig system is defined
            if at_name == 'guide':
                grp.addAttr('guide_node', at='message', multi=True)

        pm.select(self.main_node)
        pass

    def create_node(self, node_name, name='', guide_node=False):
        """
        create node
        :param node_name:
        :param name:
        :param guide_node:
        :return: created node
        @TODO make return [transform, shape] if shape exists
        """
        node = pm.createNode(node_name, name=name)
        if guide_node:
            node.message.connect(self.main_node.guide.get().guide_node)
            if isinstance(node, pm.nodetypes.DagNode):
                if isinstance(node, pm.nodetypes.Shape):
                    pass
        return node

    def del_guide(self):
        """
        delete guide group and calculation node which attached to 'guide_node' attribute
        :return:
        """
        guide = self.main_node.guide.get()
        for obj in guide.guide_node.get():
            pm.delete(obj)
        pm.delete(guide)

# class Node:
#     def __init__(self, node_name, name=''):
#         self.node = pm.createNode(node_name, name=name)
#         return self.node
#
#     def addAt(self, type='at', atName='', atRange=':', dv=0):
#         self.node.addAttr(atName,)
