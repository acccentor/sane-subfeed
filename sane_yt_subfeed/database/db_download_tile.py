from sqlalchemy import Column, Integer, Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship

from sane_yt_subfeed.database.decorators import TextPickleType
from sane_yt_subfeed.database.orm import PermanentBase, db_session
from sane_yt_subfeed.database.video import Video


class DBDownloadTile(PermanentBase):
    __tablename__ = 'download_tile'
    id = Column('id', Integer, primary_key=True)
    finished = Column(Boolean)
    started_date = Column(DateTime)
    finished_date = Column(DateTime)
    video_id = Column(String, ForeignKey('video.video_id'), unique=True)
    video = relationship('Video')
    video_downloaded = Column(Boolean)
    total_bytes = Column(Integer)
    last_event = Column(TextPickleType())
    cleared = Column(Boolean)

    def __init__(self, download_tile):
        self.finished = download_tile.finished
        self.started_date = download_tile.started_date
        self.finished_date = download_tile.finished_date
        self.video = db_session.query(Video).get(download_tile.video.video_id)
        self.video_downloaded = download_tile.video_downloaded
        self.total_bytes = download_tile.total_bytes
        self.last_event = download_tile.last_event
        self.cleared = download_tile.cleared

    def update_tile(self, download_tile):
        self.finished = download_tile.finished
        self.started_date = download_tile.started_date
        self.finished_date = download_tile.finished_date
        self.total_bytes = download_tile.total_bytes
        self.last_event = download_tile.last_event
        self.cleared = download_tile.cleared
