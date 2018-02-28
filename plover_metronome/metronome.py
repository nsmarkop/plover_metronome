'''
A metronome for keeping time.
'''

import sys
try:
    import winsound
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

from PyQt5 import QtWidgets, QtCore, Qt

from plover.gui_qt.tool import Tool
from plover_metronome.metronome_ui import Ui_Metronome


class Metronome(Tool, Ui_Metronome):
    '''
    A tool for keeping time.
    '''

    TITLE = 'Metronome'
    ICON = ':/metronome/icon.svg'
    ROLE = 'metronome'

    # Set up default state
    to_active_text: str = 'Start'
    to_inactive_text: str = 'Stop'
    is_active: bool = False
    default_bpm: int = 80
    current_bpm: int = default_bpm

    def __init__(self, engine):
        super().__init__(engine)
        self.setupUi(self)

        # Not sure why this is needed, but it keeps removing it otherwise
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, False)

        # Set up event handlers
        self.bpm_input.valueChanged.connect(self.set_current_bpm)
        self.metronome_toggle.clicked.connect(self.on_toggle_metronome)

        # Create things
        self.create_metronome_timer()
        self.create_blinker_animation()

        # Restore saved settings and default state
        self.restore_state()

        self.metronome_toggle.setText(self.to_active_text)

    def create_metronome_timer(self):
        '''
        Creates the timer the metronome will use. Does not start it.
        '''

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer)

    def create_blinker_animation(self):
        '''
        Creates the state machine for the blinker animation.
        '''

        effect = Qt.QGraphicsOpacityEffect(self.bpm_blinker)
        self.bpm_blinker.setGraphicsEffect(effect)
        self.blinker_animation = Qt.QPropertyAnimation(effect, b'opacity')
        self.blinker_animation.setStartValue(1.0)
        self.blinker_animation.setEndValue(0.0)

    '''
    State Management
    '''

    def _save_state(self, settings: QtCore.QSettings):
        '''
        Additional state to save.

        :param settings: The settings object for Qt.
        :type settings: PyQt5.QtCore.QSettings
        '''

        settings.setValue('current_bpm', self.current_bpm)

    def _restore_state(self, settings: QtCore.QSettings):
        '''
        Additional state to restore.

        :param settings: The settings object for Qt.
        :type settings: PyQt5.QtCore.QSettings
        '''

        bpm = settings.value('current_bpm', self.default_bpm, int)
        self.bpm_input.setValue(bpm)
        self.set_current_bpm(bpm)

    '''
    Static Methods
    '''

    @staticmethod
    def bpm_to_interval(bpm: int):
        '''
        Converts BPM to a timer interval in milliseconds.
        '''

        return 60 / bpm * 1000

    @staticmethod
    def make_beep():
        '''
        Makes a beeping sound.
        '''

        if IS_WINDOWS:
            winsound.Beep(440, 150)
        else:
            # Alternative to this is printing out the bell code: print('\a')
            QtWidgets.QApplication.beep()

    '''
    Event Handlers
    '''

    def set_current_bpm(self, bpm: int):
        '''
        Updates the current BPM.
        '''

        self.current_bpm = bpm

        # Update the the application
        update_interval = Metronome.bpm_to_interval(self.current_bpm)
        self.timer.setInterval(update_interval)
        self.blinker_animation.setDuration(update_interval / 2)

        self.save_state()

    def on_toggle_metronome(self):
        '''
        Toggles the metronome on / off.
        '''

        if self.is_active:
            self.timer.stop()
            self.is_active = False
            self.metronome_toggle.setText(self.to_active_text)

            # Don't stop the blinker_animation, just let it finish on its own
        else:
            self.timer.start()
            self.is_active = True
            self.metronome_toggle.setText(self.to_inactive_text)

            self.blinker_animation.start()

    def on_timer(self):
        '''
        Performs each timer interval's actions for the metronome.
        '''

        Metronome.make_beep()

        # Toggle the animation off then on to prevent visual lag
        self.blinker_animation.stop()
        self.blinker_animation.start()


# For running as standalone. No Plover functionality will work.
# Can test with `python -m plover_metronome.metronome`.
if __name__ == '__main__':
    APP = QtWidgets.QApplication(sys.argv)
    METRONOME = Metronome(None)
    METRONOME.show()
    sys.exit(APP.exec_())
