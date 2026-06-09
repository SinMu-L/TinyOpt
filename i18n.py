import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
I18N_DIR = BASE_DIR / "i18n"


class Translator:
    def __init__(self, lang="zh"):
        self._lang = lang
        self._data = {}
        self._listeners = []
        self.load(lang)

    def load(self, lang):
        self._lang = lang
        file_path = I18N_DIR / f"{lang}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except:
                self._data = {}
        else:
            self._data = {}

    def get(self, key, **kwargs):
        parts = key.split(".")
        value = self._data
        try:
            for part in parts:
                value = value[part]
        except (KeyError, TypeError):
            return key
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        return value

    def set_language(self, lang):
        self.load(lang)
        for callback in self._listeners:
            try:
                callback()
            except Exception:
                pass

    def on_change(self, callback):
        self._listeners.append(callback)

    @property
    def lang(self):
        return self._lang


_TRANSLATOR = Translator()


def set_language(lang):
    _TRANSLATOR.set_language(lang)


def get_language():
    return _TRANSLATOR.lang


def T(key, **kwargs):
    return _TRANSLATOR.get(key, **kwargs)


def on_language_change(callback):
    _TRANSLATOR.on_change(callback)
