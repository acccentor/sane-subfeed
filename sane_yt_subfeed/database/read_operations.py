import datetime
import time

from sqlalchemy import desc

from sane_yt_subfeed.controller.static_controller_vars import LISTENER_SIGNAL_NORMAL_REFRESH, \
    LISTENER_SIGNAL_DEEP_REFRESH
from sane_yt_subfeed.database.database_static_vars import ORDER_METHOD_DATE_DOWNLOADED_UPLOAD_DATE
from sane_yt_subfeed.database.detached_models.video_d import VideoD
from sane_yt_subfeed.database.engine_statements import get_video_by_vidd_stmt, get_video_by_id_stmt
from sane_yt_subfeed.database.orm import db_session, engine
from sane_yt_subfeed.database.write_operations import UpdateVideosThread
from sane_yt_subfeed.database.video import Video
from sane_yt_subfeed.youtube.thumbnail_handler import download_thumbnails_threaded
from sane_yt_subfeed.youtube.update_videos import refresh_uploads
from sane_yt_subfeed.log_handler import create_logger
from sqlalchemy.sql.expression import false, true, or_

logger = create_logger("Database (READ)")


def get_newest_stored_videos(limit, filter_downloaded=False):
    """

    :param limit:
    :param filter_downloaded:
    :return: list(VideoD)
    """
    if filter_downloaded:
        logger.info("Getting newest stored videos (filter: downloaded)")
        db_videos = db_session.query(Video).order_by(desc(Video.date_published)).filter(
            Video.downloaded != '1', Video.discarded != '1').limit(
            limit).all()
    else:
        logger.info("Getting newest stored videos")
        db_videos = db_session.query(Video).order_by(desc(Video.date_published)).limit(limit).all()
    videos = Video.to_video_ds(db_videos)
    db_session.remove()
    return videos


def get_best_downloaded_videos(limit, filter_watched=True, sort_method=ORDER_METHOD_DATE_DOWNLOADED_UPLOAD_DATE):
    """

    :param sort_method:
    :param filter_watched:
    :param limit:
    :return: list(VideoD)
    """
    db_query = db_session.query(Video)

    if sort_method == ORDER_METHOD_DATE_DOWNLOADED_UPLOAD_DATE:
        db_query = db_query.order_by(desc(Video.date_downloaded), desc(Video.date_published))

    if filter_watched:
        db_query = db_query.filter(Video.vid_path != "", or_(Video.watched.is_(None), Video.watched == false()))
    else:
        db_query = db_query.filter(Video.vid_path != "").limit(limit).all()
    db_videos = db_query.limit(limit).all()
    videos = Video.to_video_ds(db_videos)
    db_session.remove()
    return videos


def compare_db_filtered(videos, limit, discarded=False, downloaded=False):
    logger.info("Comparing filtered videos with DB")
    return_list = []
    counter = 0
    for video in videos:
        db_vid = db_session.query(Video).get(video.video_id)
        if db_vid:
            if db_vid.downloaded and downloaded:
                continue
            elif db_vid.discarded and discarded:
                continue
            else:
                return_list.append(db_vid.to_video_d(video))
                counter += 1
        else:
            return_list.append(video)
            counter += 1
        if counter >= limit:
            break
    db_session.remove()
    return return_list


def check_for_new(videos, deep_refresh=False):
    logger.info("Checking for new videos{}".format((" (deep refresh)" if deep_refresh else "")))
    # FIXME: add to progress bar
    # start_time = timeit.default_timer()
    for vid in videos:
        stmt = get_video_by_vidd_stmt(vid)
        db_video = engine.execute(stmt).first()
        if not db_video:
            vid_age = datetime.datetime.utcnow() - vid.date_published
            if deep_refresh:
                if vid_age > datetime.timedelta(hours=1):
                    vid.missed = True
                    logger.info("Missed video: {} - {} [{}]".format(vid.channel_title, vid.title, vid.url_video))
                else:
                    vid.new = True
                    logger.info("New video: {} - {} [{}]".format(vid.channel_title, vid.title, vid.url_video))
            else:
                if vid_age > datetime.timedelta(hours=12):
                    vid.missed = True
                    logger.info("Missed video: {} - {} [{}]".format(vid.channel_title, vid.title, vid.url_video))
                else:
                    vid.new = True
                    logger.info("New video: {} - {} [{}]".format(vid.channel_title, vid.title, vid.url_video))
        else:
            pass
    # print(timeit.default_timer() - start_time)
    return videos


def refresh_and_get_newest_videos(limit, filter_downloaded=False, progress_listener=None,
                                  refresh_type=LISTENER_SIGNAL_NORMAL_REFRESH):
    logger.info("Refreshing and getting newest videos")
    if progress_listener:
        progress_listener.progress_bar.setVisible(True)
        progress_listener.resetBar.emit()
    videos = refresh_uploads(progress_bar_listener=progress_listener, add_to_max=2 * limit, refresh_type=refresh_type)
    if filter_downloaded:
        return_list = compare_db_filtered(videos, limit, True, True)
    else:
        return_list = videos[:limit]

    if refresh_type == LISTENER_SIGNAL_DEEP_REFRESH:
        return_list = check_for_new(return_list, deep_refresh=True)
    else:
        return_list = check_for_new(return_list)

    UpdateVideosThread(videos).start()
    download_thumbnails_threaded(return_list, progress_listener=progress_listener)
    UpdateVideosThread(return_list, update_existing=True).start()
    if progress_listener:
        progress_listener.progress_bar.setVisible(False)
        progress_listener.resetBar.emit()
    return return_list


def get_vid_by_id(video_id):
    stmt = get_video_by_id_stmt(video_id)
    db_video = engine.execute(stmt).first()
    return db_video

def get_videos_by_ids(video_ids):
    db_videos = engine.execute(Video.__table__.select(Video.video_id.in_(video_ids)))
    return_videos = Video.to_video_ds(db_videos)
    return return_videos
