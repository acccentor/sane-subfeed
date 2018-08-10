# PyQt5
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QCheckBox, QComboBox

# Internal
from sane_yt_subfeed.config_handler import read_config, DEFAULTS, get_size, get_options
# import sane_yt_subfeed.gui.views.config_view.checkbox as checkbox
from sane_yt_subfeed.gui.views.config_view.config_items import checkbox, combobox
from sane_yt_subfeed.gui.views.config_view.config_items.checkbox import GenericConfigCheckBox
from sane_yt_subfeed.gui.views.config_view.config_items.combobox import GenericConfigComboBox
from sane_yt_subfeed.log_handler import create_logger


class ConfigViewWidget(QWidget):
    """
    Configuration widget
    """

    def __init__(self, parent, root):
        """
        A GUI Widget that reads and sets config.ini settings
        :param parent:
        :param clipboard:
        :param status_bar:
        """
        super(ConfigViewWidget, self).__init__(parent)
        self.parent = parent
        self.root = root  # MainWindow
        self.logger = create_logger(__name__)
        self.clipboard = self.root.clipboard
        self.status_bar = self.root.status_bar

        self.offset = 0
        self.layout = None
        self.deco_l = "【"
        self.deco_r = "】"

        self.init_ui()

    def init_ui(self):
        """
        Initialize UI
        :return:
        """
        self.logger.info("Initializing UI")
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.populate_options()
        mismatch = get_size() - self.offset
        if mismatch != 0:
            self.logger.warning("ConfigView is missing {} entries!".format(mismatch))

    def add_section(self, name):
        """
        Add a section to the ConfigView layout and increment grid offset.
        :return:
        """
        self.layout.addWidget(QLabel(name), self.offset, 0)
        self.offset += 1

    def add_option_checkbox(self, description, cfg_section, cfg_option):
        """
        Add an option w/ value to the ConfigView layout and increment the grid offset.
        :param cfg_option:
        :param cfg_section:
        :param description:
        :return:
        """
        option = QLabel(description)
        value = GenericConfigCheckBox(self, description, cfg_section, cfg_option)
        self.layout.addWidget(option, self.offset, 0)
        self.layout.addWidget(value, self.offset, 1)
        self.offset += 1

        return value  # Needed for connected listeners etc

    def add_option_inactive(self, description, cfg_section, cfg_option):
        """
        Add an option w/ UNEDITABLE value to the ConfigView layout and increment the grid offset.
        :param cfg_option:
        :param cfg_section:
        :param description:
        :return:
        """
        option = QLabel(description)
        value = QLabel(str(DEFAULTS[cfg_section][cfg_option]))
        self.layout.addWidget(option, self.offset, 0)
        self.layout.addWidget(value, self.offset, 1)
        self.offset += 1

        return value  # Needed for connected listeners etc

    def add_option_combobox(self, description, cfg_section, cfg_option, items):
        """
        Add an option w/ value to the ConfigView layout and increment the grid offset.
        :param numeric:
        :param items:
        :param cfg_option:
        :param cfg_section:
        :param description:
        :return:
        """
        # if numeric:
        #     items = [str(i) for i in items]
        #     if items[0] == 'Disabled':
        #         value_offset = -1
        #     elif int(items[0]) == 0:
        #         value_offset = 0
        #     elif int(items[0]) == 1:
        #         value_offset = 1
        #     else:
        #         value_offset = 1

        formated_items = [format(item) for item in items]

        option = QLabel(description)
        value = GenericConfigComboBox(self, description, cfg_section, cfg_option, formated_items)
        self.layout.addWidget(option, self.offset, 0)
        self.layout.addWidget(value, self.offset, 1)
        self.offset += 1

        return value  # Needed for connected listeners etc

    def populate_options(self):
        """
        Populate the layout with sections, options and (editable) values
        :return:
        """
        combox_w_disabled = list(range(-1, 1000))
        combox_w_disabled[0] = 'Disabled'
        thumb_qualities = ['maxres', 'standard', 'high', 'medium', 'default']
        tt_font_sizes = ['h1', 'h2', 'h3', 'h4', 'h5', 'p']

        # Section [Gui]
        self.add_section('{}GUI{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Launch GUI', 'Gui', 'launch_gui')
        self.add_option_checkbox('Hide downloaded videos from feed', 'Gui',
                                 'hide_downloaded')
        self.add_option_combobox('Grid view X', 'Gui', 'grid_view_x', list(range(1, 100)))
        self.add_option_combobox('Grid view Y', 'Gui', 'grid_view_y', list(range(1, 100)))
        self.add_option_checkbox('Grey background on old (1d+) videos', 'Gui', 'grey_old_videos')
        self.add_option_combobox('\tGrid tile height (px)', 'Gui', 'tile_pref_height', list(range(1, 1000)))
        self.add_option_combobox('\tGrid tile width (px)', 'Gui', 'tile_pref_width', list(range(1, 1000)))
        self.add_option_checkbox('Embed thumbnails in tooltips', 'Gui', 'tooltip_pictures')
        self.add_option_combobox('\tTooltip picture width', 'Gui', 'tooltip_picture_width', list(range(1, 1000)))
        self.add_option_combobox('\tTooltip picture height', 'Gui', 'tooltip_picture_height', list(range(1, 1000)))
        self.add_option_combobox('\tTooltip picture font size', 'Gui', 'tooltip_picture_size', list(range(1, 1000)))
        self.add_option_checkbox('Keep Aspect Ratop on resized thumbnails', 'Gui', 'keep_thumb_ar')
        self.add_option_checkbox('Auto copy to clipboard', 'Gui', 'enable_auto_copy_to_clipboard')

        # Section [Debug]
        self.add_section('{}Debug{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Debug prints', 'Debug', 'debug')
        self.add_option_checkbox('Cache subscriptions', 'Debug', 'cached_subs')
        self.add_option_checkbox('Start with cached videos', 'Debug', 'start_with_stored_videos')
        self.add_option_combobox('Channel limit', 'Debug', 'channels_limit', list(range(-1, 100)))
        self.add_option_checkbox('Use playlistItems', 'Debug', 'use_playlistitems')
        self.add_option_checkbox('Disable tooltips', 'Debug', 'disable_tooltips')
        self.add_option_checkbox('Disable tqdm (cli)', 'Debug', 'disable_tqdm')
        self.add_option_checkbox('Show channel grab methods', 'Debug', 'show_grab_method')
        self.add_option_checkbox('Log all YouTube API responses: search()', 'Debug', 'log_search')
        self.add_option_checkbox('Log all YouTube API responses: list()', 'Debug', 'log_list')
        self.add_option_inactive('\t Haystack needle ', 'Debug', 'log_needle')
        self.add_option_checkbox('Show unimplemented GUI elements', 'Debug', 'show_unimplemented_gui')

        # Section [Model]
        self.add_section('{}Model{}'.format(self.deco_l, self.deco_r))
        self.add_option_combobox('Videos to load by default', 'Model', 'loaded_videos', list(range(1, 1000)))

        # Section [Requests]
        self.add_section('{}Requests{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Use tests', 'Requests', 'use_tests')
        self.add_option_combobox('Missed video limit', 'Requests', 'miss_limit', list(range(0, 201)))
        self.add_option_combobox('Test pages', 'Requests', 'test_pages', list(range(0, 201)))
        self.add_option_combobox('Additional list pages', 'Requests', 'extra_list_pages', list(range(0, 201)))
        self.add_option_combobox('Deep search API quota limit per request (in K)', 'Requests', 'deep_search_quota_k',
                                 list(range(1, 1000)))
        self.add_option_combobox('Filter videos older than (days)', 'Requests', 'filter_videos_days_old',
                                 list(range(-1, 100)))

        # Section [Thumbnails]
        self.add_section('{}Thumbnails{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Force download best quality, based on prioritised list',
                                 'Thumbnails', 'force_download_best')
        self.add_option_combobox('1. Priority', 'Thumbnails', '0',  thumb_qualities)
        self.add_option_combobox('2. Priority', 'Thumbnails', '1',  thumb_qualities)
        self.add_option_combobox('3. Priority', 'Thumbnails', '2',  thumb_qualities)
        self.add_option_combobox('4. Priority', 'Thumbnails', '3',  thumb_qualities)
        self.add_option_combobox('5. Priority', 'Thumbnails', '4',  thumb_qualities)

        # Section [Threading]
        self.add_section('{}Threading{}'.format(self.deco_l, self.deco_r))
        self.add_option_combobox('Image/thumbnail download thread limit', 'Threading', 'img_threads', list(range(1, 1001)))

        # Section [Play]
        self.add_section('{}View: Playback{}'.format(self.deco_l, self.deco_r))
        self.add_option_inactive('YouTube video directory', 'Play', 'yt_file_path')
        self.add_option_checkbox('Disable directory listener (inotify)', 'Play', 'disable_dir_listener')
        self.add_option_checkbox('Use URL as path', 'Play', 'use_url_as_path')
        self.add_option_combobox('Default watch priority', 'Play', 'default_watch_prio', list(range(0, 101)))

        # Section [Youtube-dl]
        self.add_section('{}Downloading / youtube-dl{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Use youtube-dl?', 'Youtube-dl', 'use_youtube_dl')

        # Section [Youtube-dl_proxies]
        self.add_section('{}Download (geoblock failover) proxy{}'.format(self.deco_l, self.deco_r))
        _counter = 1
        for proxy in get_options('Youtube-dl_proxies'):
            self.add_option_inactive('Proxy #{}'.format(_counter), 'Youtube-dl_proxies', proxy)
            _counter += 1

        # Section [Player]
        self.add_section('{}Media player{}'.format(self.deco_l, self.deco_r))
        self.add_option_inactive('Default Player', 'Player', 'default_player')
        _counter = 1
        for alt_player in get_options('Player'):
            if _counter == 1:  # Skip default player
                _counter += 1
                continue
            self.add_option_inactive('Alternative Player #{}'.format(_counter), 'Player', alt_player)
            _counter += 1

        # Section [Logging]
        self.add_section('{}Logging{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Use socket instead of file', 'Logging', 'use_socket_log')
        self.add_option_combobox('Log level', 'Logging', 'log_level',  list(range(0, 11)))
        self.add_option_combobox('Port', 'Logging', 'logging_port',  list(range(0, 65537)))

        # Section [Toolbar]
        self.add_section('{}Toolbar{}'.format(self.deco_l, self.deco_r))
        self.add_option_checkbox('Show on-demand download video field?', 'Toolbar', 'show_download_video_field')
