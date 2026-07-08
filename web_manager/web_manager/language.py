import json
import os

class Translator:
    def __init__(self, lang_code='en_US'):
        self.lang_data = {}
        self.lang_code = lang_code
        self.load_language(lang_code)

    def load_language(self, lang_code):
        lang_file = f'{os.path.dirname(os.path.abspath(__file__))}/lang/{lang_code}.json'
        if not os.path.exists(lang_file):
            lang_file = f'{os.path.dirname(os.path.abspath(__file__))}/lang/en_US.json'
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.lang_data = json.load(f)
        except FileNotFoundError:
            raise Exception(f"Language {lang_file} file {lang_code}.json not found!")

    def translate(self, key, **kwargs):
        message = self.lang_data.get(key, key)
        if not kwargs:
            return message
        try:
            return message.format(**kwargs)
        except KeyError:
            return message


translator = Translator()
