from PyQt5.QtCore import Qt  # PyCharm bug: Anything from QtCore will fail detection, but it *is* there.
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QCheckBox

from sane_yt_subfeed.config_handler import set_config


# ######################################################################## #
# ################################# [GUI] ################################ #
# ######################################################################## #

class GenericConfigCheckBox(QCheckBox):
    def __init__(self, parent, description, cfg_section, cfg_option):
        super(QCheckBox, self).__init__(parent=parent)
        self.cfg_parent=parent
        self.description = description
        self.cfg_section = cfg_section
        self.cfg_option = cfg_option

        self.setCheckState(2 if self.cfg_parent.input_read_config(cfg_section, cfg_option) else 0)

        self.stateChanged.connect(self.save_option)

    def save_option(self, state):
        if state == Qt.Checked:
            set_config(self.cfg_section, self.cfg_option, 'True')
        else:
            set_config(self.cfg_section, self.cfg_option, 'False')
