function getSearchTerm()
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++)
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == 'q')
        {
            return sParameterName[1];
        }
    }
}

$(function() {

    var initialise_search = function(){
        require.config({"baseUrl":"/mkdocs/js"});
        require(["search",]);
    }

    var search_term = getSearchTerm();
    if(search_term){
        $('#mkdocs_search_modal').modal();
    }

    $('pre code').parent().addClass('prettyprint well');

    $(document).on("submit", "#mkdocs_search_modal form", function (e) {
        $("#mkdocs-search-results").html("Searching...");
        initialise_search();
        return false;
    });

});
