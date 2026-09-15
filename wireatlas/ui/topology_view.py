from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class TopologyView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)