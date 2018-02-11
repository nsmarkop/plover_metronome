'''
A metronome for keeping time.
'''

import sys
try:
    import winsound
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

from PyQt5 import QtWidgets, QtGui, QtCore, Qt

# TODO:
# from plover_metronome.dock_tool import DockTool
from plover.gui_qt.tool import Tool
from plover_metronome.metronome_ui import Ui_Metronome
# from dock_tool import DockTool
# from metronome_ui import Ui_Metronome


class Metronome(Tool, Ui_Metronome):
    '''
    A tool for keeping time
    '''

    TITLE = 'Metronome'
    ROLE = 'metronome'

    # Set up default state
    to_active_text: str = 'Start'
    to_inactive_text: str = 'Stop'
    is_active: bool = False
    max_bpm: int = 400
    min_bpm: int = 1
    default_bpm: int = 80
    current_bpm: int = default_bpm
    blinker_is_on: bool = False

    def __init__(self, engine):
        super().__init__(engine)
        self.setupUi(self)

        # Not sure why this is needed, but it keeps removing it otherwise
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, False)

        # Set up event handlers
        self.increase_button.clicked.connect(self.on_increase_bpm)
        self.decrease_button.clicked.connect(self.on_decrease_bpm)
        self.metronome_toggle.clicked.connect(self.on_toggle_metronome)
        self.bpm_input.textEdited.connect(self.on_bpm_text_changed)
        self.bpm_input.returnPressed.connect(self.on_bpm_text_entered)

        # Set up validators
        self.bpm_input.setValidator(QtGui.QIntValidator(self.min_bpm, self.max_bpm))

        # Create things
        self.create_metronome_timer()
        self.create_blinker_animation()

        # Restore saved settings, particularly important is the BPM
        self.restore_state()
        self.set_current_bpm(self.current_bpm)

        # Set up remaining state.
        # TODO: self.update_blinker(False)
        self.metronome_toggle.setText(self.to_active_text)
        self.update_bpm_text(str(self.current_bpm))

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
        # TODO:
        # effect = Qt.QGraphicsColorizeEffect(self.bpm_blinker)
        # self.bpm_blinker.setGraphicsEffect(effect)
        # self.blinker_animation = Qt.QPropertyAnimation(effect, b'color')
        # self.blinker_animation.setStartValue(Qt.QColor(125, 125, 0, 1))
        # self.blinker_animation.setEndValue(Qt.QColor(125, 125, 0, 0))

    def set_current_bpm(self, bpm: int):
        '''
        Updates the current BPM.
        '''

        # Clamp the BPM value within our restricted range
        self.current_bpm = clamp(bpm, self.min_bpm, self.max_bpm)

        # Update the the application
        update_interval = Metronome.bpm_to_interval(self.current_bpm)
        self.timer.setInterval(update_interval)
        self.blinker_animation.setDuration(update_interval / 2)

        self.update_bpm_buttons()
        self.save_state()

    '''
    Overrides
    '''
    # TODO:
    # def closeEvent(self, event: Qt.QCloseEvent):
    #     '''
    #     Override of the default closing event to save state.

    #     :param event: The Qt closing event.
    #     :type event: PyQt5.Qt.QCloseEvent
    #     '''

    #     self.save_state()

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

        self.current_bpm = settings.value('current_bpm', self.default_bpm, int)

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
            # An alternative to this would be printing out the bell code: print('\a')
            QtWidgets.QApplication.beep()

    '''
    Event Handlers
    '''

    def on_increase_bpm(self):
        '''
        Increases the current BPM.
        '''

        self.set_current_bpm(self.current_bpm + 1)
        self.update_bpm_text(str(self.current_bpm))

    def on_decrease_bpm(self):
        '''
        Decreases the current BPM.
        '''

        self.set_current_bpm(self.current_bpm - 1)
        self.update_bpm_text(str(self.current_bpm))

    def on_toggle_metronome(self):
        '''
        Toggles the metronome on / off.
        '''

        if self.is_active:
            self.timer.stop()
            self.is_active = False
            self.metronome_toggle.setText(self.to_active_text)

            # TODO: self.update_blinker(False)
        else:
            self.timer.start()
            self.is_active = True
            self.metronome_toggle.setText(self.to_inactive_text)

            # TODO: self.update_blinker(True)
            self.blinker_animation.start()


    def on_bpm_text_changed(self, bpm: str):
        '''
        Updates the state with the new BPM.

        :param bpm: The BPM that was changed to.
        :type bpm: str
        '''

        try:
            self.set_current_bpm(int(bpm))
        except (TypeError, ValueError):
            pass

    def on_bpm_text_entered(self):
        '''
        When return or enter are pressed on the BPM input, clear focus.
        '''

        self.bpm_input.clearFocus()

    def on_timer(self):
        '''
        Performs each timer interval's actions for the metronome.
        '''

        Metronome.make_beep()
        self.blinker_animation.stop()
        self.blinker_animation.start()

    '''
    UI Updating
    '''

    def update_bpm_text(self, text: str):
        '''
        Updates the BPM display text.

        :param text: The text to update to.
        :type text: str
        '''

        try:
            self.bpm_input.setText(text)
        except TypeError:
            pass

    def update_bpm_buttons(self):
        '''
        Updates the BPM buttons to make sure they're valid in the current state.
        '''

        if self.current_bpm <= self.min_bpm:
            self.decrease_button.setEnabled(False)
            self.increase_button.setEnabled(True)
        elif self.current_bpm >= self.max_bpm:
            self.increase_button.setEnabled(False)
            self.decrease_button.setEnabled(True)
        else:
            self.decrease_button.setEnabled(True)
            self.increase_button.setEnabled(True)

    def update_blinker(self, is_on: bool):
        '''
        Updates the state of the blinker.

        :param is_on: If the blinker should be on or off.
        :type is_on: bool
        '''

        self.bpm_blinker.setVisible(is_on)

def clamp(value: int, min_value: int, max_value: int):
    '''
    Clamps a value within a range.

    :param value: The value to clamp.
    :type value: int

    :param min_value: The minimum value of the range.
    :type min_value: int

    :param max_value: The maximum value of the range.
    :type max_value: int

    :returns: The clamped value.
    :rtype: int
    '''

    if value < min_value:
        return min_value
    elif value > max_value:
        return max_value

    return value

# For running as standalone. No Plover functionality will work when run this way.
if __name__ == '__main__':
    APP = QtWidgets.QApplication(sys.argv)
    METRONOME = Metronome(None)
    METRONOME.show()
    sys.exit(APP.exec_())
