import requests


class TelegramApi:

    TELEGRAM_BASE_URL = 'https://api.telegram.org'

    @classmethod
    def _get(cls, token: str, method: str, **kwargs):
        return requests.get(url=f'{cls.TELEGRAM_BASE_URL}/bot{token}/{method}', params=kwargs)

    @classmethod
    def get_up_path(cls, token: str, file_id: str):
        return cls._get(token=token, method='getFile', file_id=file_id)
