$(document).ready(function(){

    $(".my-accordion-header-bar").click(function(evt) {
        var container = $(this).closest(".my-accordion-section");
        var content = container.find(".my-accordion-content");
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

});