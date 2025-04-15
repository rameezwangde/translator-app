from flask import Flask, render_template, request
from langdetect import detect
from deep_translator import GoogleTranslator
import re
import os

app = Flask(__name__)

# Language code mapping
LANGUAGES = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic', 'hy': 'Armenian', 'az': 'Azerbaijani',
    'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
    'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English', 'eo': 'Esperanto',
    'et': 'Estonian', 'tl': 'Filipino', 'fi': 'Finnish', 'fr': 'French', 'gl': 'Galician', 'ka': 'Georgian',
    'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole', 'ha': 'Hausa', 'haw': 'Hawaiian',
    'iw': 'Hebrew', 'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian', 'is': 'Icelandic', 'ig': 'Igbo',
    'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian', 'ja': 'Japanese', 'jw': 'Javanese', 'kn': 'Kannada',
    'kk': 'Kazakh', 'km': 'Khmer', 'ko': 'Korean', 'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz', 'lo': 'Lao',
    'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian', 'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
    'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori', 'mr': 'Marathi', 'mn': 'Mongolian',
    'my': 'Myanmar (Burmese)', 'ne': 'Nepali', 'no': 'Norwegian', 'ps': 'Pashto', 'fa': 'Persian', 'pl': 'Polish',
    'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan', 'gd': 'Scots Gaelic',
    'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak',
    'sl': 'Slovenian', 'so': 'Somali', 'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish',
    'tg': 'Tajik', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish', 'uk': 'Ukrainian',
    'ur': 'Urdu', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa', 'yi': 'Yiddish',
    'yo': 'Yoruba', 'zu': 'Zulu'
}

# Idioms and their meanings
IDIOM_DICT = {
    "spill the beans": "reveal a secret",
    "kick the bucket": "die",
    "piece of cake": "very easy",
    "break the ice": "start a conversation",
    "raining cats and dogs": "raining heavily",
    "once in a blue moon": "very rarely",
    "hit the sack": "go to sleep",
    "burn the midnight oil": "stay up late working"
}

# Heuristic-based idiom detection and replacement (no NLP libs)
def preprocess_idioms(text):
    lowered_text = text.lower()
    replacements = []

    for idiom, meaning in IDIOM_DICT.items():
        idiom_pattern = r'\b' + re.escape(idiom) + r'\b'
        matches = list(re.finditer(idiom_pattern, lowered_text, flags=re.IGNORECASE))

        for match in matches:
            idiom_text = match.group()
            start, end = match.start(), match.end()
            left_context = lowered_text[max(0, start - 60):start]
            right_context = lowered_text[end:end + 60]

            if is_idiomatic_use(idiom, left_context, right_context):
                text = re.sub(idiom_pattern, meaning, text, count=1, flags=re.IGNORECASE)
                replacements.append((idiom_text, meaning))
                break  # only one idiom per sentence

    return text, replacements


def is_idiomatic_use(idiom, left_context, right_context):
    context = left_context + " " + idiom + " " + right_context

    if idiom == "piece of cake":
        if re.search(r'\b(was|is|seems|looks like|felt like)\b.*piece of cake', context):
            return True
        if re.search(r'\ba piece of cake\b', context):
            return False
        return False

    if idiom == "kick the bucket":
        if re.search(r'\b(he|she|they|i)\b.*\bkicked the bucket\b', context):
            return True
        if re.search(r'\b(kicks|kicking|kick) the bucket\b.*(across|into|toward)', context):
            return False
        return True

    if idiom == "spill the beans":
        return bool(re.search(r'\b(spill|spilled)\s+the beans\b', context))

    if idiom == "raining cats and dogs":
        return True

    if idiom == "once in a blue moon":
        return True

    if idiom == "burn the midnight oil":
        return bool(re.search(r'\b(burn|burned)\s+the midnight oil\b', context))

    if idiom == "hit the sack":
        return bool(re.search(r'\b(hit|hits|hitting)\s+the sack\b', context))

    return False

# Translation logic
def detect_and_translate(text, target_lang):
    try:
        processed_text, replacements = preprocess_idioms(text)
        detected_lang = detect(processed_text)
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(processed_text)
        return detected_lang, translated_text, replacements
    except Exception as e:
        print("Translation error:", e)
        return "unknown", "Translation failed. Please try again.", []


# Routes
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', languages=LANGUAGES)

@app.route('/trans', methods=['POST'])
def trans():
    text = request.form.get('text')
    target_lang = request.form.get('target_lang')
    detected_lang = ""
    translation = ""
    replacements = []

    if text and target_lang:
        detected_lang, translation, replacements = detect_and_translate(text, target_lang)

    return render_template('index.html',
                           translation=translation,
                           detected_lang=detected_lang,
                           replacements=replacements,
                           languages=LANGUAGES)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)












