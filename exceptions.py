class DropConnectionExc(Exception):
    def __init__(self):
        super().__init__('Connection dropperd')
