function fetchDefinition() {
    var term = document.getElementById('id_term').value;
    var language = document.getElementById('id_language').value;
    var url = '/api/define.json?term=' + term + '&language=' + language;

    fetch(url)
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        var definitionInput = document.getElementById('id_definition');
        definitionInput.value = data.definition;

        // If the term already exists, disable the textarea and add a link to
        // the page for editing it.
        if (data.edit_link) {
            definitionInput.disabled = true;
            var definitionEdit = document.getElementById('definition_edit');
            definitionEdit.className = '';
            definitionEdit.href = data.edit_link;
        } else {
            definitionInput.disabled = false;
            document.getElementById('definition_edit').className = 'hidden';
        }
    });
}
