# !/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from subprocess import check_output

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QMenu, QStackedWidget

# Project internal libs
from sane_yt_subfeed.absolute_paths import ICO_PATH, VERSION_PATH
from sane_yt_subfeed.config_handler import read_config, set_config
from sane_yt_subfeed.controller.listeners import LISTENER_SIGNAL_NORMAL_REFRESH, LISTENER_SIGNAL_DEEP_REFRESH
from sane_yt_subfeed.controller.static_controller_vars import GRID_VIEW_ID, PLAY_VIEW_ID
from sane_yt_subfeed.controller.view_models import MainModel
from sane_yt_subfeed.gui.dialogs.input_dialog import SaneInputDialog
from sane_yt_subfeed.gui.dialogs.text_view_dialog import TextViewDialog
from sane_yt_subfeed.gui.main_window.db_state import DbStateIcon
from sane_yt_subfeed.gui.main_window.toolbar import Toolbar
from sane_yt_subfeed.gui.views.about_view import AboutView
from sane_yt_subfeed.gui.views.config_view.config_window import ConfigWindow
from sane_yt_subfeed.gui.views.config_view.views.config_view import ConfigViewWidget
from sane_yt_subfeed.gui.views.config_view.views.hotkeys_view import HotkeysViewWidget
from sane_yt_subfeed.gui.views.grid_view.grid_scroll_area import GridScrollArea
from sane_yt_subfeed.gui.views.grid_view.play_view.play_view import PlayView
from sane_yt_subfeed.gui.views.grid_view.sub_feed.sub_feed_view import SubFeedView
from sane_yt_subfeed.gui.views.list_detailed_view import ListDetailedView
from sane_yt_subfeed.gui.views.list_tiled_view import ListTiledView
from sane_yt_subfeed.gui.views.subscriptions_view import SubscriptionsView
from sane_yt_subfeed.history_handler import get_history
from sane_yt_subfeed.log_handler import create_logger


# Constants



class MainWindow(QMainWindow):
    current_view = None
    grid_view = None
    subs_view = None
    list_detailed_view = None
    list_tiled_view = None
    about_view = None
    menus = None
    hotkey_ctrl_down = False

    # noinspection PyArgumentList
    def __init__(self, main_model: MainModel, dimensions=None, position=None):
        super().__init__()
        self.logger = create_logger(__name__)
        self.main_model = main_model

        self.clipboard = QApplication.clipboard()
        self.status_bar = self.statusBar()
        self.menus = {}
        if dimensions:
            self.dimensions = dimensions
        else:
            self.dimensions = [770, 700]
        self.position = position
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.grid_view = GridScrollArea(self, main_model)
        self.play_view = GridScrollArea(self, main_model)
        self.grid_view.set_view(SubFeedView(self.grid_view, self, main_model), GRID_VIEW_ID)
        self.play_view.set_view(PlayView(self.play_view, self, main_model), PLAY_VIEW_ID)

        self.config_view = ConfigWindow(self)
        self.hotkeys_view = ConfigWindow(self)
        self.config_view.setWidget(ConfigViewWidget(self.config_view, self))
        self.hotkeys_view.setWidget(HotkeysViewWidget(self.hotkeys_view, self))

        self.list_detailed_view = ListDetailedView(self)
        self.list_tiled_view = ListTiledView(self)
        self.subs_view = SubscriptionsView(self)
        self.about_view = AboutView(self)

        self.init_ui()

    def init_ui(self):
        self.logger.info("Initialized UI")
        # Define a menu and status bar
        menubar = self.menuBar()
        self.statusBar()

        # File menu
        self.add_menu(menubar, '&File')
        self.add_submenu('&File', 'Download by URL/ID', self.download_single_url_dialog, shortcut='Ctrl+O',
                         tooltip='Download a video by URL/ID')
        self.add_submenu('&File', 'View history', self.usage_history_dialog, shortcut='Ctrl+H',
                         tooltip='Show usage history in a dialog box')
        self.add_submenu('&File', 'Preferences', self.view_config, shortcut='Ctrl+P',
                         tooltip='Change application settings', icon='preferences.png')
        self.add_submenu('&File', 'Exit', qApp.quit, shortcut='Ctrl+Q', tooltip='Exit application')

        # Function menu
        self.add_menu(menubar, '&Function')

        # Set function menu triggers
        self.add_submenu('&Function', 'Copy all URLs', self.clipboard_copy_urls, shortcut='Ctrl+D',
                         tooltip='Copy URLs of all currently visible videos to clipboard', icon='copy.png')

        # refresh_list
        # self.add_submenu('&Function', 'Refresh Feed', self.refresh_list, shortcut='Ctrl+R',
        #                  tooltip='Refresh the subscription feed'
        refresh_feed = self.add_submenu('&Function', 'Refresh Feed', self.refresh_list, shortcut='Ctrl+R',
                                        tooltip='Refresh the subscription feed', icon='refresh.png')

        self.add_submenu('&Function', 'Reload Subscriptions &List', self.refresh_subs, shortcut='Ctrl+L',
                         tooltip='Fetch a new subscriptions list', icon='refresh_subs.png')

        # FIXME: icon, shortcut(alt/shift as extra modifier to the normal refresh shortcut?)
        self.add_submenu('&Function', 'Deep refresh of feed', self.refresh_list_deep, shortcut='Ctrl+T',
                         tooltip='Deed refresh the subscription feed', icon='refresh.png')

        self.add_submenu('&Function', 'Test Channels', self.test_channels,
                         tooltip='Tests the test_pages and miss_limit of channels', icon='rerun_test.png')

        self.add_submenu('&Function', 'Manual dir search', self.dir_search,
                         tooltip='Starts a manual search for new videos in youtube directory',
                         icon='folder_refresh.png')

        thumb_tooltip = 'Starts a manual download of thumbnails for videos currently in play view and sub feed'
        self.add_submenu('&Function', 'Manual thumbnail download', self.thumbnail_download,
                         tooltip=thumb_tooltip, icon='folder_refresh.png')

        self.add_submenu('&Function', 'Manual DB grab', self.db_reload,
                         tooltip='Starts a manual grab of data for the model', icon='database.png', shortcut='Ctrl+E')

        # FIXME: icon, look more related to action
        self.add_submenu('&Function', 'Toggle ascending date', self.toggle_ascending_sort,
                         tooltip='Toggles the ascending date config option, and does a manual re-grab',
                         icon='database.png', shortcut='Ctrl+A')

        # get_single_video = self.add_submenu('&Function', 'Get video', self.get_single_video,
        #                                     tooltip='Fetch video by URL')

        # View menu
        self.add_menu(menubar, '&View')
        view_grid_view = self.add_submenu('&View', 'Subscription feed', self.view_grid, shortcut='Ctrl+1',
                                          tooltip='View subscription feed as a grid', icon='grid.png')
        view_play_view = self.add_submenu('&View', 'Playback feed', self.view_play, shortcut='Ctrl+2',
                                          tooltip='View downloaded videos as a grid',
                                          icon='play_view_basic.png')
        view_list_detailed_view = self.add_submenu('&View', 'Detailed List', self.view_list_detailed, shortcut='Ctrl+3',
                                                   tooltip='View subscription feed as a detailed list',
                                                   icon='table.png')
        if read_config('Debug', 'show_unimplemented_gui'):
            view_list_tiled_view = self.add_submenu('&View', 'Tiled List', self.view_list_tiled, shortcut='Ctrl+4',
                                                    tooltip='View subscription feed as a tiled list',
                                                    icon='tiled_list.png')
        view_subs_view = self.add_submenu('&View', 'Subscriptions', self.view_subs, shortcut='Ctrl+5',
                                          tooltip='View Subscriptions', icon='subs.png')

        # Help menu
        self.add_menu(menubar, '&Help')
        self.add_submenu('&Help', 'Hotkeys', self.view_hotkeys, shortcut='F2',
                         tooltip='View hotkeys')
        if read_config('Debug', 'show_unimplemented_gui'):
            view_about_view = self.add_submenu('&Help', 'About', self.view_about, shortcut='F1', tooltip='About me',
                                               icon='about.png')

        toolbar = Toolbar(self)
        self.addToolBar(toolbar)
        toolbar.addAction(view_grid_view)
        toolbar.addAction(view_play_view)
        toolbar.addAction(view_list_detailed_view)
        if read_config('Debug', 'show_unimplemented_gui'):  # FIXME: Implement
            toolbar.addAction(view_list_tiled_view)
        toolbar.addAction(view_subs_view)
        if read_config('Debug', 'show_unimplemented_gui'):
            toolbar.addAction(view_about_view)

        toolbar.create_action_group()
        # not included in exclusive action group
        toolbar.addAction(refresh_feed)

        # Set MainWindow properties
        app_title = 'Sane Subscription Feed'
        version = self.determine_version()
        if version:
            app_title += " v{}".format(version)
        self.setWindowTitle(app_title)
        self.setWindowIcon(QIcon(os.path.join(ICO_PATH, 'yubbtubbz-padding.ico')))
        self.statusBar().showMessage('Ready.')

        progress_bar = self.main_model.new_status_bar_progress(self)
        # progress_bar.setFixedHeight(20)
        progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(progress_bar)
        self.statusBar().addPermanentWidget(DbStateIcon(toolbar, self.main_model))

        # # Set a default view and layout
        # window_layout = QVBoxLayout()
        # self.view_grid()
        # self.setLayout(window_layout)

        # Display the window
        self.central_widget.addWidget(self.grid_view)
        self.central_widget.addWidget(self.play_view)
        self.central_widget.addWidget(self.list_detailed_view)
        if read_config('Debug', 'show_unimplemented_gui'):
            self.central_widget.addWidget(self.list_tiled_view)
        self.central_widget.addWidget(self.subs_view)
        if read_config('Debug', 'show_unimplemented_gui'):
            self.central_widget.addWidget(self.about_view)
        # self.central_widget.addWidget(self.hotkeys_view)
        self.central_widget.setCurrentWidget(self.grid_view)

        # if self.dimensions:
        #     self.resize(self.dimensions[0], self.dimensions[1])

    # Qt Overrides
    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Control:
            # self.logger.debug("ctrl pressed")
            self.hotkey_ctrl_down = True

    def keyReleaseEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Control:
            # self.logger.debug("ctrl released")
            self.hotkey_ctrl_down = False

    # Internal
    def determine_version(self):
        """
        Attempt to determine current release version based on VERSION.txt (and git)
        :return:
        """
        version_str = None
        git_branchtag = self.get_git_tag()
        try:
            with open(VERSION_PATH, 'r') as version_file:
                version = version_file.readline()
                if git_branchtag:
                    version_str = "{} [{}]".format(str(version), git_branchtag)
                else:
                    version_str = str(version)
        except:  # FIXME: PEP8 -- Too broad except clause
            pass

        return version_str

    def get_git_tag(self):
        """
        Gets git branch/commit_tag if in a git environment
        :return:
        """
        branchtag = None
        try:
            branchtag = check_output("git rev-parse --abbrev-ref HEAD", shell=True).decode("UTF-8").strip('\n') + ' / '
        except:  # FIXME: PEP8 -- Too broad except clause
            pass
        try:
            branchtag += check_output("git log -n 1 --pretty=format:%h", shell=True).decode("UTF-8").strip('\n')
        except:  # FIXME: PEP8 -- Too broad except clause
            pass

        return branchtag

    # Menu handling
    def add_menu(self, menubar, name):
        """
        Adds a menu and an optional amount of submenus
        :param menubar:
        :param name:
        :return:
        """
        self.menus[name] = menubar.addMenu(name)

    def add_submenu(self, menu, name, action, shortcut=None, tooltip=None, icon=None):
        """
        Adds a submenu with optional properties to a menu
        :param name:
        :param icon: icon filename (with relative path)
        :param tooltip: String
        :param action: Function
        :param shortcut: String on the form of '<key>+...n+key>' e.g. 'Ctrl+1'
        :param menu:
        :return:
        """
        if icon:
            this_icon = QIcon(os.path.join(ICO_PATH, icon))
            submenu = QAction(this_icon, name, self)
        else:
            submenu = QAction(name, self)
        if shortcut:
            submenu.setShortcut(shortcut)
        if tooltip:
            submenu.setStatusTip(tooltip)

        submenu.triggered.connect(action)
        if menu in self.menus:
            self.menus[menu].addAction(submenu)
        else:
            raise ValueError("add_submenu('{}', '{}', ...) ERROR: '{}' not in menus dict!".format(menu, name, menu))
        return submenu  # FIXME: Used by toolbar to avoid redefining items

    @staticmethod
    def hide_widget(widget):  # TODO: Deferred usage (Garbage collection issue)
        """
        Hides a widget/view
        :param widget:
        :return:
        """
        widget.setHidden(True)

    def view_grid(self):
        """
        Set View variable and CentralWidget to GridView
        :return:
        """
        # FIXME: hotfix for actions using self.grid_view(refresh and copy urls)
        self.central_widget.setCurrentWidget(self.grid_view)

    def view_play(self):
        """
        Set View variable and CentralWidget to GridView
        :return:
        """
        # FIXME: hotfix for actions using self.grid_view(refresh and copy urls)
        self.central_widget.setCurrentWidget(self.play_view)

    def view_subs(self):
        """
        Set View variable and CentralWidget to SubscriptionsView
        :return:
        """
        self.central_widget.setCurrentWidget(self.subs_view)

    def view_list_detailed(self):
        """
        Set View variable and CentralWidget to ListDetailedView
        :return:
        """
        self.central_widget.setCurrentWidget(self.list_detailed_view)

    def view_list_tiled(self):
        """
        Set View variable and CentralWidget to ListTiledView
        :return:
        """
        self.central_widget.setCurrentWidget(self.list_tiled_view)

    def view_config(self):
        """
        Set View variable and CentralWidget to ConfigView
        :return:
        """
        self.config_view.show()
        # self.central_widget.setCurrentWidget(self.config_view)

    def view_about(self):
        """
        Set View variable and CentralWidget to AboutView
        :return:
        """
        self.central_widget.setCurrentWidget(self.about_view)

    def view_hotkeys(self):
        """
        Set View variable and CentralWidget to HotkeysView
        :return:
        """
        self.hotkeys_view.show()

    # Function menu functions
    def clipboard_copy_urls(self):
        """
        Adds the url of each video in the view to a string, separated by newline and puts it on clipboard.
        :return:
        """
        grid_items = 20
        urls = ""
        for q_label in self.grid_view.q_labels:
            urls += "{}\n".format(q_label.video.url_video)

        self.logger.info("Copied URLs to clipboard: \n{}".format(urls))
        self.clipboard.setText(urls)
        self.statusBar().showMessage('Copied {} URLs to clipboard'.format(len(urls.splitlines())))

    def refresh_list(self):
        """
        Refresh the subscription feed
        :return:
        """
        self.main_model.main_window_listener.refreshVideos.emit(LISTENER_SIGNAL_NORMAL_REFRESH)

    def refresh_list_deep(self):
        """
        Refresh the subscription feed
        :return:
        """
        self.main_model.main_window_listener.refreshVideos.emit(LISTENER_SIGNAL_DEEP_REFRESH)

    def test_channels(self):
        """
        Sends a testChannels signal
        :return:
        """
        self.main_model.main_window_listener.testChannels.emit()

    def dir_search(self):
        """
        Sends a testChannels signal
        :return:
        """
        self.main_model.yt_dir_listener.manualCheck.emit()
        # do_walk(os.path.join("d:/", "youtube"))

    def thumbnail_download(self):
        """
        Sends a testChannels signal
        :return:
        """
        self.main_model.grid_view_listener.thumbnailDownload.emit()
        # do_walk(os.path.join("d:/", "youtube"))

    def db_reload(self):
        """
        Sends a testChannels signal
        :return:
        """
        self.main_model.grid_view_listener.updateFromDb.emit()

    def toggle_ascending_sort(self):
        """
        Sends a testChannels signal
        :return:
        """
        toggle = read_config('PlaySort', 'ascending_date')
        set_config('PlaySort', 'ascending_date', format(not toggle))
        self.main_model.grid_view_listener.updateFromDb.emit()

    def refresh_subs(self):
        """
        Fetch a new list of subscriptions
        :return:
        """
        self.main_model.main_window_listener.refreshSubs.emit()

    def get_single_video(self, input_text):
        """
        Download a single video based on input
        :param input_text: URL or ID
        :return:
        """
        self.logger.debug(
            "get_single_video({}) called self.main_model.main_window_listener.getVideo.emit()".format(input_text))
        self.main_model.main_window_listener.getSingleVideo.emit(input_text)

    def download_single_url_dialog(self):
        """
        Prompts user for downloading a video by URL/ID
        :return:
        """
        input_dialog = SaneInputDialog(self, self, title='Download a video by URL/ID', label='URL/ID:',
                                       ok_button_text='Download')
        input_dialog.show()

    def usage_history_dialog(self):
        """
        Pop-up a TextViewDialog with usage history
        :return:
        """
        history = get_history()
        history_dialog = TextViewDialog(self, history)
        history_dialog.setWindowTitle("Usage history")
        history_dialog.show()

    # Unused functions
    def context_menu_event(self, event):  # TODO: Unused, planned usage in future
        """
        Context menu for right clicking video thumbnails and more.
        :param event:
        :return:
        """
        cmenu = QMenu(self)
        copy_link_action = cmenu.addAction("Copy link")
        open_link_action = cmenu.addAction("Open link")
        close_action = cmenu.addAction("Close")
        action = cmenu.exec_(self.mapToGlobal(event.pos()))

    # Misc cleanup handling
    @staticmethod
    def clear_layout(layout):  # TODO: Unused
        """
        Deletes the given layout
        :param layout:
        :return:
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()