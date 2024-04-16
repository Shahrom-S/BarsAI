import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import re

nltk.download('punkt')
nltk.download('stopwords')


class SystemController:
    def __init__(self):
        self.volume = self.get_volume_control()
        self.commands = {
            "increase volume": self.increase_volume,
            "decrease volume": self.decrease_volume,
            "mute": self.mute_volume,
            "unmute": self.unmute_volume,
        }
        self.stop_words = set(stopwords.words('english'))

    def get_volume_control(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return volume

    def increase_volume(self, amount=10):
        current_volume = self.volume.GetMasterVolumeLevelScalar()
        new_volume = min(current_volume + amount / 100.0, 1.0)
        self.volume.SetMasterVolumeLevelScalar(new_volume, None)

    def decrease_volume(self, amount=10):
        current_volume = self.volume.GetMasterVolumeLevelScalar()
        new_volume = max(current_volume - amount / 100.0, 0.0)
        self.volume.SetMasterVolumeLevelScalar(new_volume, None)

    def mute_volume(self):
        self.volume.SetMute(1, None)

    def unmute_volume(self):
        self.volume.SetMute(0, None)

    def process_command(self, command):
        command = command.lower()
        tokens = word_tokenize(command)
        filtered_tokens = [word for word in tokens if word.isalnum() and word not in self.stop_words]
        filtered_command = ' '.join(filtered_tokens)

        for key in self.commands:
            if re.search(key, filtered_command):
                amount = self.extract_amount(filtered_command)
                if amount:
                    self.commands[key](amount)
                else:
                    self.commands[key]()
                break

    def extract_amount(self, command):
        match = re.search(r'\d+', command)
        return int(match.group()) if match else None


if __name__ == "__main__":
    controller = SystemController()
    while True:
        user_command = input("Enter command: ")
        controller.process_command(user_command)