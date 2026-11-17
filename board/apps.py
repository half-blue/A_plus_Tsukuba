from django.apps import AppConfig


class BoardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'board'

    def ready(self):
        # 新着をモデレーション用の Discord に知らせるシグナルを登録する (board/signals.py)
        from . import signals  # noqa: F401
