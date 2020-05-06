from moviepy.editor import AudioFileClip
import subprocess
import base64
import tempfile
import shutil
import os
import base64
import uuid
import psutil
import speech_recognition as sr
from syncit.constants import Constants
import logging
from syncit.constants import Constants
from logger_setup import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


class Converter():
    """
    Class designed to make all the conversions and merges between video and audio.

    Attributes:
        audio (str): Path to audio file.
        tmpdir (str): Persistent temporary folder (if created).
    """

    def __init__(self, audio_file):
        """
        Constructor of Converter.

        Params:
            audio_file (FileStorage): Object with the video file loaded.
        """

        self.tmpdir = tempfile.mkdtemp()
        self.audio = self.convert_filestorage_to_file(audio_file)
        self.repair_audio_file()

    def convert_filestorage_to_file(self, audio_file):
        """
        Converts FileStorage object to a file. Stores it in temporary location and returns it's path.

        Params:
            video_file (FileStorage): Object with the video file loaded.
            extension (str): The file extension.

        Returns:
            str: Path to video file.
        """

        filename = f'{uuid.uuid4().hex[:10]}.{Constants.RECIEVED_AUDIO_FILE_EXTENSION}'
        path = os.path.join(self.tmpdir, filename)
        logger.debug(f'Converting FileStorage to file. path: {path}')
        with open(path, 'wb') as f:
            try:
                f.write(audio_file.read())
            except Exception as e:
                logger.error(f'Unable to convert FileStorage to file. Error: {e}')
        
        logger.debug(f'Finished converting FileStorage to file.')
        return path

    def repair_audio_file(self):
        """
        Repairs the audio file loaded in self.audio
        The frontend gives compressed audio file, moviepy can create a new repaired file
        that will work with the speech recognition.

        Re sets the path.
        """
        
        logger.debug('Repairing audio file')
        clip = AudioFileClip(self.audio)
        filename = f'{uuid.uuid4().hex[:10]}.{Constants.DESIRED_AUDIO_FILE_EXTENSION}'
        path = os.path.join(self.tmpdir, filename)
        logger.debug(f'Repairing audio file. New path: {path}')
        clip.write_audiofile(path)
        try:
            os.remove(self.audio)
            logger.debug(f'Removed file {self.audio}')
        except:
            logger.warning(f'Unable to remove file {self.audio}.')
        self.audio = path

    def convert_audio_to_text(self, start=None, end=None, hot_word=None):
        """
        Converts audio file to text. Can be of specific timestamp or with hot word.

        Params:
            start (float): OPTIONAL: start time.
            end (float): OPTIONAL: end time.
            hot_word (str): OPTIONAL: hot word to look for.

        Returns:
            str: The required transcript.
        """

        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(self.audio)          

        with audio_file as source:
            if(start is not None and end is not None):
                duration = end - start
                audio = recognizer.record(
                    source, offset=start, duration=duration)
            else:
                audio = recognizer.record(source)

        try:
            if(hot_word):
                transcript = recognizer.recognize_sphinx(
                    audio, 'en-US', [(hot_word, 1)])
            else:
                transcript = recognizer.recognize_sphinx(audio)
            return transcript

        # Empty transcript
        except sr.UnknownValueError:
            return ''

        except Exception as e:
            logger.error(f'Unknown Error while recognizing. Error: {e}')
            return ''

    def clean(self):
        """
        Deletes the temporary folder, if created.
        """

        
        if(self.tmpdir):
            try:
                shutil.rmtree(self.tmpdir)
            except:
                logger.warning(f'Unable to clean up.')
