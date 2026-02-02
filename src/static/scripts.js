function slugify(text) {
    /* this comes from stack overflow lol
    https://stackoverflow.com/questions/54743952/javascript-slug-working-for-non-latin-characters-also
    */
    text = text.toLowerCase().trim();
    const sets = [
        {to: 'a', from: '[ÀÁÂÃÄÅÆĀĂĄẠẢẤẦẨẪẬẮẰẲẴẶἀ]'},
        {to: 'c', from: '[ÇĆĈČ]'},
        {to: 'd', from: '[ÐĎĐÞ]'},
        {to: 'e', from: '[ÈÉÊËĒĔĖĘĚẸẺẼẾỀỂỄỆ]'},
        {to: 'g', from: '[ĜĞĢǴ]'},
        {to: 'h', from: '[ĤḦ]'},
        {to: 'i', from: '[ÌÍÎÏĨĪĮİỈỊ]'},
        {to: 'j', from: '[Ĵ]'},
        {to: 'ij', from: '[Ĳ]'},
        {to: 'k', from: '[Ķ]'},
        {to: 'l', from: '[ĹĻĽŁ]'},
        {to: 'm', from: '[Ḿ]'},
        {to: 'n', from: '[ÑŃŅŇ]'},
        {to: 'o', from: '[ÒÓÔÕÖØŌŎŐỌỎỐỒỔỖỘỚỜỞỠỢǪǬƠ]'},
        {to: 'oe', from: '[Œ]'},
        {to: 'p', from: '[ṕ]'},
        {to: 'r', from: '[ŔŖŘ]'},
        {to: 's', from: '[ßŚŜŞŠȘ]'},
        {to: 't', from: '[ŢŤ]'},
        {to: 'u', from: '[ÙÚÛÜŨŪŬŮŰŲỤỦỨỪỬỮỰƯ]'},
        {to: 'w', from: '[ẂŴẀẄ]'},
        {to: 'x', from: '[ẍ]'},
        {to: 'y', from: '[ÝŶŸỲỴỶỸ]'},
        {to: 'z', from: '[ŹŻŽ]'},
        {to: '-', from: '[·/_,:;\']'}
  ];

  sets.forEach(set => {
    text = text.replace(new RegExp(set.from,'gi'), set.to)
  });

  return text
    .replace(/\s+/g, '-')    // Replace spaces with -
    .replace(/[^-a-zа-я\u0370-\u03ff\u1f00-\u1fff]+/g, '') // Remove all non-word chars
    .replace(/--+/g, '-')    // Replace multiple - with single -
    .replace(/^-+/, '')      // Trim - from start of text
    .replace(/-+$/, '')      // Trim - from end of text
}


function fillSlugFromInput(inputName, inputPrefix) {
    var value = document.getElementById('id_' + inputPrefix + inputName).value;
    document.getElementById('id_' + inputPrefix + 'slug').value = slugify(value);
}


function fixOcr(elementId) {
    var field = document.getElementById(elementId);
    var lines = field.value.split(/\n/g);

    var newLines = [];
    var newLine = [];
    var line, nextLine, n;
    for (var i = 0; i < lines.length; i++) {
        line = lines[i];
        if (i == lines.length - 1) {
            nextLine = '';
        } else {
            nextLine = lines[i+1];
        }

        n = line.length;
        if (n > 0) {
            if (line[n-1] === '-' && (n == 1 || line[n-2] != '-')) {
                // Get rid of the -.
                newLine.push(line.substring(0, n-1) + nextLine);
                i++;
            } else {
                newLine.push(line);
            }
        } else {
            // Preserve the empty line.
            newLines.push(newLine.join(' '));
            newLines.push('');
            newLine = [];
        }
    }
    if (newLine) {
        newLines.push(newLine.join(' '));
    }

    var newValue = newLines.join('\n');
    // replace various things
    var replacements = {
        ' o f ': ' of ',
        '­ ': '',
    };
    var key, regex, replace;
    for (key in replacements) {
        regex = new RegExp(key, 'g');
        replace = replacements[key];
        newValue = newValue.replace(regex, replace);
    }
    field.value = newValue;
}

function reformatSubject(elementId) {
    var field = document.getElementById(elementId);
    const subject = field.value.trim();
    if (subject) {
        field.value = subject[0].toLowerCase() + subject.substring(1);
    }
}

function reformatQuote(elementId) {
    var field = document.getElementById(elementId);
    var lines = field.value.split(/\n/g);

    var newLines = [];
    var newLine = [];
    var line, nextLine, n;
    for (var i = 0; i < lines.length; i++) {
        line = lines[i];
        if (i == lines.length - 1) {
            nextLine = '';
        } else {
            nextLine = lines[i+1];
        }

        n = line.length;
        if (n > 0) {
            if (line[n-1] === '-' && (n == 1 || line[n-2] != '-')) {
                // Get rid of the -.
                newLine.push(line.substring(0, n-1) + nextLine);
                i++;
            } else {
                newLine.push(line);
            }
        } else {
            // Preserve the empty line.
            newLines.push(newLine.join(' '));
            newLines.push('');
            newLine = [];
        }
    }
    if (newLine) {
        newLines.push(newLine.join(' '));
    }

    field.value = newLines.join('\n');
}


function suggestTerms() {
    var term = document.getElementById('id_term-text').value;
    var url = '/api/suggest.json?term=' + term;

    if (term.length >= 3) {
        fetch(url).then(
            function (response) {
                return response.json();
            }
        ).then(
            function (data) {
                var terms = data.terms;
                var row;
                var labels = [];

                if (terms.length) {
                    for (var i = 0; i < terms.length; i++) {
                        row = terms[i];
                        labels.push(
                            '<div class="item">' + row.text + ' - ' +
                            row.language + '</div>'
                        );
                    }
                    $('#suggested-terms').html(labels.join(''));
                    $('#suggested-terms').show();
                } else {
                    $('#suggested-terms').html('');
                }
            }
        )
    } else {
        $('#suggested-terms').html('');
    }
}

$('#suggested-terms').on('click', '.item', function() {
    var details = $(this).text().split(' - ');
    var lang = details[1];  // may not always work lol
    var term = details[0];

    $('#id_term-text').val(term);
    $('#id_term-language').val(lang);

    $('#suggested-terms').html('');
    $('#suggested-terms').hide();
    fetchDefinition();
});


function fetchDefinition() {
    var term = document.getElementById('id_term-text').value;
    var language = document.getElementById('id_term-language').value;
    var url = '/api/define.json?term=' + term + '&language=' + language;

    fetch(url)
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        var definitionInput = document.getElementById('id_term-definition');
        var highlightsInput = document.getElementById('id_term-highlights');
        var newCheckbox = document.getElementById('id_occurrence-is_new');
        definitionInput.value = data.definition;
        highlightsInput.value = data.highlights;

        var linkButton = document.getElementById('link_button');
        var occurrencesCount = document.getElementById('occurrences_count');

        // If the term already exists, disable the definition and highlights
        // textareas, disable the 'new' checkbox, and add a link to the page
        // for viewing it.
        if (data.view_link) {
            linkButton.className = 'ui blue button';
            linkButton.href = data.view_link;

            newCheckbox.disabled = true;

            occurrencesCount.innerText = '(' + data.num_occurrences + ' occurrences)';

            // Also set the category to 'notable'.
            document.getElementById('id_occurrence-category').value = '1';
        } else {
            newCheckbox.disabled = false;
            definitionInput.disabled = false;
            highlightsInput.disabled = false;
            linkButton.className = 'ui disabled button';
            occurrencesCount.innerText = '';
        }
        $('#suggested-terms').hide();
        $('#suggested-terms').html('');
    });
}

function toggleIsReadFields(isRead) {
    // toggleClass takes an optional second param, a boolean which adds if true
    // and removes if not
    // If the book is read, hide the due date and priority etc
    $('.only-if-unread').toggleClass('disabled', isRead);
    $('.only-if-read').toggleClass('disabled', !isRead);
};

$('.editable-rating').rating({
    maxRating: 5,
    interactive: true,
    onRate: function(value) {
        $('#rating-input').val(value);
    }
});

$('.display-rating').rating({
    maxRating: 5,
    interactive: false,
});

$('.ui.dropdown').dropdown({fullTextSearch: 'exact'});
$('.ui.checkbox').checkbox();

// Enable or disable fields on the book form page acc to the is-read checkbox
$('#is-read-checkbox input').change(function() {
    toggleIsReadFields(this.checked);
});
// so ugly lol
if ($('#is-read-checkbox').length) {
    // making it variable in case I stop checking it by default
    var isRead = $('#is-read-checkbox input').attr('checked');
    toggleIsReadFields(isRead);
}

$('#site-search').search({
    // change search endpoint to a custom endpoint by manipulating apiSettings
    apiSettings: {
      url: '/search.json?q={query}'
    },
    type: 'category',
    minCharacters: 3
  })
;
