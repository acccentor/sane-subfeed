from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea

from sane_yt_subfeed.controller.static_controller_vars import PLAY_VIEW_ID, GRID_VIEW_ID
from sane_yt_subfeed.controller.view_models import MainModel
from sane_yt_subfeed.gui.views.download_view.download_view import DownloadView


class DownloadScrollArea(QScrollArea):

    def __init__(self, parent, model: MainModel):
        super(DownloadScrollArea, self).__init__(parent)

        self.parent = parent
        self.model = model
        self.widget = None
        self.widget_id = None

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.resize(100, 100)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalScrollBar().setEnabled(False)
        self.current_v_max = self.verticalScrollBar().maximum()

        self.widget = DownloadView(self)
        self.setWidget(self.widget)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Home:
            self.verticalScrollBar().setValue(0)
        elif event.key() == Qt.Key_End:
            # FIXME: do something with auto reload so that this is not needed
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum() - 1)

    # def set_view(self, widget, widget_id):
    #     self.widget_id = widget_id
    #     self.widget = widget
    #     self.setWidget(widget)
