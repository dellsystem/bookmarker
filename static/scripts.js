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
