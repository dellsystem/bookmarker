window.onkeydown = function (e) {
    if (e.code === 'Escape') {
        const focused = document.activeElement;
        const elems = ['INPUT', 'TEXTAREA'];
        if (elems.includes(focused.tagName)) {
            focused.blur();
        }
    }
};

var shortcuts = new Set();
function labelShortcut(shortcut, label) {
    if (shortcuts.has(shortcut)) {
        return false;
    }
    
    $('#keyboard-shortcuts .content').append(
        '<h3 class="ui header">' + shortcut + ': ' + label + '</h3>'
    );
    shortcuts.add(shortcut);
    return true;
}

function bindModalShortcut(shortcut, label, element) {
    if (labelShortcut(shortcut, label)) {
        Mousetrap.bind(shortcut, function() {
            $(element).modal({
                onApprove: function() {
                    $(element).find('form').submit();
                }
            }).modal('show');
        });
        return true;
    }
    return false;
}


function bindClickShortcut(shortcut, label, element) {
    if (labelShortcut(shortcut, label)) {
        Mousetrap.bind(shortcut, function() {
            element.click();
        });
        return true;
    }
    return false;
}

/* GLOBAL SHORTCUTS/MODAL SEARCH */
Mousetrap.bind('?', function() {
    $('#keyboard-shortcuts').modal('show');
});

$('.json-search').each(function() {
    const searchType = $(this).data('search-type') || 'standard';
    const searchUrl = $(this).data('search-url');
    $(this).search({
        apiSettings: {
            url: searchUrl + '?q={query}'
        },
        type: searchType,
        searchOnFocus: false,
        maxResults: 3,
        minCharacters: 3
    });
});

/* PAGE-SPECIFIC SHORTCUTS/MODAL SEARCH */
$('.modal-keyboard-shortcut').each(function () {
    const label = $(this).data('label');
    const shortcut = $(this).data('shortcut');
    bindModalShortcut(shortcut, label, this);
});

$('.keyboard-shortcut').each(function () {
    const label = $(this).data('label');
    const shortcut = $(this).data('shortcut');
    if (bindClickShortcut(shortcut, label, this)) {
        $(this).popup({title: shortcut}).popup('show');
    }
});
