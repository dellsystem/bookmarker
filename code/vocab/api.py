from merriam_webster.api import CollegiateDictionary, WordNotFoundException
from translate.translate import translate_word


DICTIONARY = CollegiateDictionary('d59bdd56-d417-42d7-906e-6804b3069c90')


def lookup_term(language, term):
    # If the language is English, use the Merriam-Webster API.
    # Otherwise, use WordReference.
    if language == 'en':
        try:
            response = DICTIONARY.lookup(term)
        except WordNotFoundException as e:
            # If the word can't be found, use the suggestions as the
            # definition.
            return e.message

        definitions = [
            u'({function}) {d}'.format(function=entry.function, d=d)
            for entry in response
            for d, _ in entry.senses
        ]
    else:
        results = translate_word('{}en'.format(language), term)
        definitions = []
        if results != -1:
            for row in results:
                # Replace linebreaks with semicolons.
                definitions.append(row[1].replace(' \n', '; ').strip())

    return ' / '.join(definitions)
