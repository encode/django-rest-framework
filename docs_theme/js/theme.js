var getSearchTerm = function() {
  var sPageURL = window.location.search.substring(1);
  var sURLVariables = sPageURL.split('&');
  for (var i = 0; i < sURLVariables.length; i++) {
    var sParameterName = sURLVariables[i].split('=');
    if (sParameterName[0] === 'q') {
      return sParameterName[1];
    }
  }
};

$(function() {
  var searchTerm = getSearchTerm(),
    $searchModal = $('#mkdocs_search_modal'),
    $searchQuery = $searchModal.find('#mkdocs-search-query'),
    $searchResults = $searchModal.find('#mkdocs-search-results');

  $('pre code').parent().addClass('prettyprint well');

  if (searchTerm) {
    $searchQuery.val(searchTerm);
    $searchResults.text('Searching...');
    $searchModal.modal();
  }

  $searchModal.on('shown', function() {
    $searchQuery.focus();
  });
});
