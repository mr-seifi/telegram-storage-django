from django.conf import settings
from django.core.files.storage import Storage
from .exceptions import *
from .models import PathMapping
from telegram import Bot
from _helpers import TelegramApi
from string import digits, ascii_letters
import random


class TelegramStorage(Storage):

    def __init__(self):
        if not hasattr(settings, 'TELEGRAM_STORAGE_OPTIONS'):
            raise SettingsNameError('TELEGRAM_STORAGE_OPTIONS does not exist.')
        if not settings.TELEGRAM_STORAGE_OPTIONS.get('TOKEN'):
            raise TokenDoesNotExist
        if not settings.TELEGRAM_STORAGE_OPTIONS.get('CHANNEL_ID'):
            raise ChannelIdDoesNotExist

        self.options = settings.TELEGRAM_STORAGE_OPTIONS

    def _get_bot(self) -> Bot:
        return Bot(token=self.options['TOKEN'])

    def _get_bot_token(self) -> str:
        return self.options['TOKEN']

    def _get_channel_id(self):
        return self.options['CHANNEL_ID']

    @staticmethod
    def _generate_random_3_letter_word():
        return ''.join(random.choices(digits + ascii_letters, k=3))

    def open(self, name, mode="rb"):
        try:
            pm = PathMapping.objects.get(filename=name)
            pm.update_accessed()
        except PathMapping.DoesNotExist:
            raise FilePathDoesNotExist(f'{name} does not exist.')

        bot = self._get_bot()
        return bot.get_file(file_id=pm.fileid)

    def save(self, name, content, max_length=None):
        bot = self._get_bot()

        try:
            name = self._prevent_same_name(name)
            up_response = bot.send_document(
                chat_id=self._get_channel_id(),
                document=content,
                filename=name
            )

            response = TelegramApi.get_up_path(token=self._get_bot_token(), file_id=up_response.document.file_id)
            if response.status_code != 200:
                raise TelegramConnectionError()
            response = response.json()

            if not response['ok'] or not response['result']:
                raise TelegramConnectionError()

            response = response.get('result')
            up_path = response.get('file_path')

        except Exception as e:
            raise TelegramConnectionError(e)

        PathMapping.objects.create(
            filename=name,
            filepath=self.path(name),
            filesize=content.size,
            fileid=response['file_id'],
            up_path=up_path
        )

        return name

    def path(self, name):
        return f'/{name}'

    def delete(self, name):
        try:
            pm = PathMapping.objects.get(filename=name)
            message_id = pm.message_id
        except PathMapping.DoesNotExist:
            raise FileDoesNotExist()

        try:
            bot = self._get_bot()
            bot.delete_message(chat_id=self._get_channel_id(),
                               message_id=message_id)
        except Exception as e:
            raise TelegramConnectionError(e)

    def exists(self, name):
        return PathMapping.objects.filter(filename=name).exists()

    def listdir(self, path):
        return list(PathMapping.objects.filter(filepath__contains=path).values_list('filename'))

    def size(self, name):
        try:
            PathMapping.objects.get(filename=name).filesize
        except PathMapping.DoesNotExist:
            raise FileDoesNotExist()

    @staticmethod
    def _up_url(name):
        try:
            return PathMapping.objects.get(filename=name).up_path
        except PathMapping.DoesNotExist:
            raise FileDoesNotExist()

    def _prevent_same_name(self, name, init=True):
        if self.exists(name):
            extension = name.split('.')[-1]
            name = ''.join(name.split('.')[:-1])
            if not init:
                name = ''.join(name.split('_')[:-1])

            return self._prevent_same_name(f'{name}_{self._generate_random_3_letter_word()}.{extension}', init=False)
        return name

    def url(self, name):
        return f'{TelegramApi.TELEGRAM_BASE_URL}/file/bot{self._get_bot_token()}/{self._up_url(name)}'

    def get_accessed_time(self, name):
        try:
            return PathMapping.objects.get(filename=name).accessed
        except PathMapping.DoesNotExist:
            raise FileDoesNotExist()

    def get_created_time(self, name):
        try:
            return PathMapping.objects.get(filename=name).created
        except PathMapping.DoesNotExist:
            raise FileDoesNotExist()

    def get_modified_time(self, name):
        try:
            return PathMapping.objects.get(filename=name).modified
        except PathMapping.DoesNotExist:
            raise FileDoesNotExist()
