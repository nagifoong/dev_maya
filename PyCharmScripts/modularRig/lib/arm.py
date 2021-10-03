from ..main import Base


class Arm(Base):
    def __init__(self):
        super(Base, self).__init__()

    def create(self):
        Base.create_node('implicitSphere', name='', guide_node=True)