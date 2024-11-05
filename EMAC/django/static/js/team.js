$(document).ready(function(){

    $(".emaccordion-header-bar").click(function(evt) {
        var container = $(this).closest(".emaccordion-section");
        var content = container.find(".emaccordion-content");
        var caret = container.find(".caret");

        if (caret.hasClass("caret-flip")) {
            caret.removeClass("caret-flip");
        } else {
            caret.addClass("caret-flip");
        }

        if (container.hasClass("expanded")) {
            container.removeClass("expanded");
        } else {
            container.addClass("expanded");
        }

        content.slideToggle(200);
    });

    // any personal url links
    $('div.team_container').on('click', 'a.personal-url', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var team_member_name = $(this).text();
        getOutboundLink($(this).attr('href'), 'team_member_personal_link', null, null, { team_member_name });
    });

});