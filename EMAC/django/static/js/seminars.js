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


    $('.schedule-tab').click(function() {
        if ($(this).hasClass('open')) {
            return;
        } else {
            var idx = $(this).index();
            $(this).closest('.schedule-tab-container').find('.schedule-tab.open').removeClass('open');
            $(this).closest('.schedule-tab-container').next('.schedule-grids').find('.schedule-day.open').removeClass('open');
            $(this).addClass('open');
            var menuSection = $(this).closest('.schedule-tab-container').next('.schedule-grids').find('.schedule-day').get(idx);
            $(menuSection).addClass('open');
        }
    });

    $('.schedule-table .detail:not(:empty)').closest('tr').addClass('has-detail');
    $('.schedule-table .youtube-link:not(:empty)').closest('tr').addClass('has-video');

    function openDetailModal(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        // clear the modal
        $('#detail-modal .date-time').text('');
        $('#detail-modal .detail-title').text('').removeClass('with-icon');
        $('#detail-modal .detail-speaker').text('').removeClass('hidden');
        $('#detail-modal .detail-description').text('');
        // get the new data
        var row = $(evt.target).closest('tr');
        var day = $('.schedule-tab.open span.hide-for-small-only').text();
        var time = $(row).find('td.time').text();
        var title = $(row).find('span.event-title').text();
        var speaker = $(row).find('span.speaker').text();
        var detail = $(row).find('.detail').html();
        var videoLink = $(row).find('.youtube-link').attr('href');
        // populate the modal
        $('#detail-modal .date-time').text(`${day}, ${time} US EST (GMT -05:00)`);
        if (videoLink) {
            title = `<span>${title}</span><a href="${videoLink}" class="youtube-link" title="Watch on YouTube"><i class="fa fa-youtube-play"></i></a>`;
            $('#detail-modal .youtube-link').text(videoLink);
            $('#detail-modal .detail-title').addClass('with-icon');
        }
        $('#detail-modal .detail-title').html(title);
        if (speaker) {
            $('#detail-modal .detail-speaker').text(`Speaker: ${speaker}`);
        } else {
            $('#detail-modal .detail-speaker').addClass('hidden');
        }
        $('#detail-modal .detail-description').html(detail);
        // open
        $('#detail-modal').foundation('open');
    }

    $('.schedule-grid-tabs').on('click', 'tr.has-detail a.open-abstract', openDetailModal);

    $('.schedule-grid-tabs').on('click', 'tr.has-video a.youtube-link', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var talk_title = $(this).closest('td').prev('td').find('span.event-title').text();
        getOutboundLink($(this).attr('href'), 'workshop_youtube_link', null, null, { talk_title });
    });

    $('div#detail-modal').on('click', '.detail-title a.youtube-link', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var talk_title = $(this).prev('span').text();
        getOutboundLink($(this).attr('href'), 'workshop_youtube_link', null, null, { talk_title });
    });

    // any links in the talk abstract detail
    $('div#detail-modal').on('click', 'div.detail-description > a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var talk_title = $(this).closest('div.detail-description').prevAll('div.detail-title').find('span').text();
        getOutboundLink($(this).attr('href'), 'workshop_abstract_link', null, null, { talk_title });
    });

    // any links in the exoVAST text
    $('div.exovast-container').on('click', 'a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var type = 'exovast_description_link';
        var alt_params = {};
        if ($(this).hasClass('youtube-link')) {
            type = 'exovast_youtube_link';
            alt_params.talk_title = $(this).closest('td').prev('td').text();
        }
        getOutboundLink($(this).attr('href'), type, null, null, alt_params);
    });

    // workshop redirect, expand old workshop section
    if (window.location.hash.toLowerCase().includes('workshop')) {
        // close everything that is not the emac workshop section
        $('div.emaccordion-content:not(.emac)').prev('.emaccordion-header-bar').click();
        // open the emac workshop section
        $('div.emaccordion-content.emac').prev('.emaccordion-header-bar').click();
    }
});