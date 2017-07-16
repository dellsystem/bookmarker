function reformatQuote() {
    var field = document.getElementById('id_note-quote');
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
        definitionInput.value = data.definition;
        highlightsInput.value = data.highlights;

        var linkButton = document.getElementById('link_button');
        var occurrencesCount = document.getElementById('occurrences_count');

        // If the term already exists, disable the definition and highlights
        // textareas and add a link to the page for viewing it.
        if (data.view_link) {
            linkButton.className = 'ui blue button';
            linkButton.href = data.view_link;

            occurrencesCount.innerText = '(' + data.num_occurrences + ' occurrences)';

            // Also set the category to 'notable'.
            document.getElementById('id_occurrence-category').value = '1';
        } else {
            definitionInput.disabled = false;
            highlightsInput.disabled = false;
            linkButton.className = 'ui disabled button';
            occurrencesCount.innerText = '';
        }
        $('#suggested-terms').hide();
        $('#suggested-terms').html('');
    });
}

$('.editable-rating').rating({
    maxRating: 5,
    interactive: true,
    onRate: function(value) {
        $('#section_rating').val(value);
    }
});

$('.display-rating').rating({
    maxRating: 5,
    interactive: false,
});

$('.multi-select').dropdown();
