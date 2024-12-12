$(document).ready(function() {
    $('div.developers.main-content').on('click', 'div.callout a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var link_title = $(this).text();
        getOutboundLink($(this).attr('href'), 'for_developers_link', null, null, { link_title });
    });
});