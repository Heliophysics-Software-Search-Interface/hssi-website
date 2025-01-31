var HSSI = HSSI || {};
HSSI.spinner = null;
HSSI.errors = [];
HSSI.linkIssues = [];

$(document).ready(function() {

    if (window.location.host === 'main_hssi_website.com') {
        $('div.scan-container').empty();
        $('div.scan-container').text('Sorry, this page is only available in a Development environment.');
        return;
    }

    $('button#scan-all-links').on('click', function() {
        var loader = document.getElementById('loading_modal');
        HSSI.spinner = HSSI.spinner || new Spin.Spinner();
        HSSI.spinner.spin(loader);
        $(loader).addClass('visible');

        HSSI.errors = [];
        HSSI.linkIssues = [];
        $('div#scan-results').empty();
        $('div#error-list').empty();

        var resourceIDs = [];
        $('div.resource-name').each(function(){
            resourceIDs.push($(this).attr('id'));
        });
        
        HSSI.scanAllResourceLinks(resourceIDs).then(function () {
            if (HSSI.linkIssues.length === 0) {
                $('div#scan-results').html('<span>No link issues found!</span>');
            } else {
                var html = '<span>Link issues found with:</span><ul>';
                HSSI.linkIssues.forEach(function(resourceId) {
                    var name = $(`div[id=${resourceId}]`).text();
                    html += `<li><a href="#${resourceId}">${name}</a></li>`;
                });
                html += '</ul>';
                $('div#scan-results').html(html);
            }
            if (HSSI.errors.length > 0) {
                var errorHtml = '<span>Additionl errors:</span><ul>';
                HSSI.errors.forEach(function(error) {
                    var name = $(`div[id=${error.resourceID}]`).text();
                    errorHtml += `<li><a href="#${error.resourceID}">${name}</a>: ${error.error}</li>`;
                });
                errorHtml += `</ul><span>Check HSSI.errors in the console for details.</span>`;
                $('div#error-list').html(errorHtml);
            }
            $(loader).removeClass('visible');
            HSSI.spinner.stop();
        });
    });

    $('div#resource-links-list').on('click', 'button.scan', function() {
        var loader = document.getElementById('loading_modal');
        HSSI.spinner = HSSI.spinner || new Spin.Spinner();
        HSSI.spinner.spin(loader);
        $(loader).addClass('visible');

        var resourceId = $(this).prev().attr('id');
        var project = $(this).prev().text();
        $('div#scan_message').text(`Scanning ${project}`);
        HSSI.scanResourceLinks(resourceId).then(function () {
            $(loader).removeClass('visible');
            HSSI.spinner.stop();
            $('div#scan_message').empty();
        });
    });
});

HSSI.scanResourceLinks = function scanResourceLinks(resourceId) {
    var dfd = $.Deferred();
    $.ajax({
        url: `?id=${resourceId}`,
        method: 'GET'
    }).done(function (response) {
        var parent = $(`div[id=${resourceId}]`).closest('div.resource-links');
        $(parent).find('table').remove();
        var newTable = $(response.links_table).find('table')
        $(parent).append(newTable);
        var issuesFound = false;
        $(newTable).find('td.status-code').each(function () {
            var statusCode = $(this).text();
            if(!isNaN(parseInt(statusCode))) {
                var href = $(this).find('a').attr('href');
                $(this).find('a').attr('href', `${href}/${statusCode}`);
            }
            if (statusCode && statusCode !== '200') {
                $(this).closest('tr').addClass('not-ok');
                issuesFound = true;
            }
        });
        if (issuesFound) {
            HSSI.linkIssues.push(resourceId);
        }
    }).fail(function (xhr, status, error) {
        console.warn(status)
        console.warn(error)
        HSSI.errors.push({
            xhr,
            status,
            error,
            resourceID: resourceId
        });
    }).always(function(){
        dfd.resolve();
    })
    return dfd.promise();
}

HSSI.scanAllResourceLinks = async function scanAllResourceLinks(resourceIDs) {
    var current = 1;
    var total = resourceIDs.length;
    for (var resourceId of resourceIDs) {
        var project = $(`div[id=${resourceId}]`).text();
        $('div#scan_message').text(`Scanning ${project} (resource ${current} of ${total})`);

        var delay = HSSI.getRandomDelayTime();
        await new Promise(res => setTimeout(res, delay));
        await HSSI.scanResourceLinks(resourceId);
        current++;
    }
    $('div#scan_message').empty();
    console.log('DONE!');
    return true;
}

HSSI.getRandomDelayTime = () => {
    var min = 200; // milliseconds
    var max = 1000; // milliseconds
    return Math.floor(Math.random() * (max - min) + min);
}