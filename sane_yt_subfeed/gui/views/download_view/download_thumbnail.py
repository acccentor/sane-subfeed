from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel


class DownloadThumbnailWidget(QLabel):

    def __init__(self, parent, video):
        super(DownloadThumbnailWidget, self).__init__(parent=parent)
        self.sane_parent = parent
        self.video = video
        self.base_thumbnail = QPixmap(self.video.thumbnail_path)
        self.thumbnail = None

        self.thumbnail = self.base_thumbnail.scaled(
            QSize(self.sane_parent.width() * 0.4, self.sane_parent.height() * 0.7),
            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.setPixmap(self.thumbnail)
