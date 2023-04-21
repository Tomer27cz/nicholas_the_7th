import json
import translators.server as server

"""
This is a program that checks if all the keys in languages.json match

if not, it translates them 
and then saves the new .json file
"""


with open('src/languages.json') as f:
    x = json.load(f)

languages = x.keys()

en_keys = x['en'].keys()

to_translate = []

for lang in languages:
    print(f"----------------------- {lang} -----------------------")
    lang_keys = x[lang].keys()
    for key in en_keys:
        if key not in lang_keys:
            to_translate.append(key)
            print(f"{key}")

result = []
for key in to_translate:
    if key not in result:
        result.append(key)

print("----------------------------------------------")
print("Results:")

print(result)

if not result:
    print("Nothing to translate!")
    exit()

print("Translating...")

for lang in languages:
    print(f"----------------------- {lang} -----------------------")
    if lang != 'en':
        for key in result:
            trans_val = server.google(x['en'][key], to_language=lang, from_language='en')
            x[lang][key] = trans_val
            print(f"{x['en'][key]} = {trans_val}")
    else:
        print("Skipping English")

print("----------------------------------------------")
print("Writing to file...")

with open('src/languages.json', 'w') as f:
    f.write(json.dumps(x, indent=4))

print("----------------------------------------------")

print("Done!")


