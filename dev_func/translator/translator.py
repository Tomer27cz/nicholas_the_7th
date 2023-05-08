import json
import os
import six
from google.cloud import translate_v2 as translate
from google.auth.credentials import Credentials

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'

"""
This is a program that checks if all the keys in languages.json match

if not, it translates them 
and then saves the new .json file
"""

# translator = Translator()

def get_to_translate(xdata, xlanguages, xen_keys):
    to_translate = []

    for xlang in xlanguages:
        print(f"----------------------- {xlang} -----------------------")
        xlang_keys = xdata[xlang].keys()
        for xkey in xen_keys:
            if xkey not in xlang_keys:
                to_translate.append(xkey)
                print(f"{xkey}")

    result = []
    for ckey in to_translate:
        if ckey not in result:
            result.append(ckey)

    print("----------------------------------------------")
    print("Results:")

    print(result)

    if not result:
        print("Nothing to translate!")
        exit()

    return result

def translate_text_google_cloud(text, target, source='en'):
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """

    translate_client = translate.Client()

    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    translation_result = translate_client.translate(text, target_language=target, source_language=source)

    return translation_result["translatedText"]

# def translate_text(text, target, source='en'):
#     trans_result= translator.translate(text, dest=target, src=source).text
#     return trans_result


with open('../../src/languages.json') as f:
    x = json.load(f)

languages = x.keys()
en_keys = x['en'].keys()

result = get_to_translate(x, languages, en_keys)

print("Translating...")

for lang in languages:
    print(f"----------------------- {lang} -----------------------")
    if lang != 'en':
        for key in result:
            trans_val = translate_text_google_cloud(x['en'][key], lang)
            x[lang][key] = trans_val
            print(f"{x['en'][key]} = {trans_val}")
    else:
        print("Skipping English")

print("----------------------------------------------")
print("Writing to file...")

with open('../../src/languages.json', 'w') as f:
    f.write(json.dumps(x, indent=4))

print("----------------------------------------------")

print("Done!")


