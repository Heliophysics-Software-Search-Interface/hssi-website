var EMAC = EMAC || {};
EMAC.spinner = null;
EMAC.errors = [];
EMAC.linkIssues = [];

$(document).ready(function() {

    if (window.location.host === 'emac.gsfc.nasa.gov') {
        $('div.scan-container').empty();
        $('div.scan-container').text('Sorry, this page is only available in a Development environment.');
        return;
    }

    $('button#scan-all-links').on('click', function() {
        var loader = document.getElementById('loading_modal');
        EMAC.spinner = EMAC.spinner || new Spin.Spinner();
        EMAC.spinner.spin(loader);
        $(loader).addClass('visible');

        EMAC.errors = [];
        EMAC.linkIssues = [];
        $('div#scan-results').empty();
        $('div#error-list').empty();

        var resourceIDs = [];
        $('div.resource-name').each(function(){
            resourceIDs.push($(this).attr('id'));
        });
        
        EMAC.scanAllResourceLinks(resourceIDs).then(function () {
            if (EMAC.linkIssues.length === 0) {
                $('div#scan-results').html('<span>No link issues found!</span>');
            } else {
                var html = '<span>Link issues found with:</span><ul>';
                EMAC.linkIssues.forEach(function(resourceId) {
                    var name = $(`div[id=${resourceId}]`).text();
                    html += `<li><a href="#${resourceId}">${name}</a></li>`;
                });
                html += '</ul>';
                $('div#scan-results').html(html);
            }
            if (EMAC.errors.length > 0) {
                var errorHtml = '<span>Additionl errors:</span><ul>';
                EMAC.errors.forEach(function(error) {
                    var name = $(`div[id=${error.resourceID}]`).text();
                    errorHtml += `<li><a href="#${error.resourceID}">${name}</a>: ${error.error}</li>`;
                });
                errorHtml += `</ul><span>Check EMAC.errors in the console for details.</span>`;
                $('div#error-list').html(errorHtml);
            }
            $(loader).removeClass('visible');
            EMAC.spinner.stop();
        });
    });

    $('div#resource-links-list').on('click', 'button.scan', function() {
        var loader = document.getElementById('loading_modal');
        EMAC.spinner = EMAC.spinner || new Spin.Spinner();
        EMAC.spinner.spin(loader);
        $(loader).addClass('visible');

        var resourceId = $(this).prev().attr('id');
        var project = $(this).prev().text();
        $('div#scan_message').text(`Scanning ${project}`);
        EMAC.scanResourceLinks(resourceId).then(function () {
            $(loader).removeClass('visible');
            EMAC.spinner.stop();
            $('div#scan_message').empty();
        });
    });
});

EMAC.scanResourceLinks = function scanResourceLinks(resourceId) {
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
            EMAC.linkIssues.push(resourceId);
        }
    }).fail(function (xhr, status, error) {
        console.warn(status)
        console.warn(error)
        EMAC.errors.push({
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

EMAC.scanAllResourceLinks = async function scanAllResourceLinks(resourceIDs) {
    var current = 1;
    var total = resourceIDs.length;
    for (var resourceId of resourceIDs) {
        var project = $(`div[id=${resourceId}]`).text();
        $('div#scan_message').text(`Scanning ${project} (resource ${current} of ${total})`);

        var delay = EMAC.getRandomDelayTime();
        await new Promise(res => setTimeout(res, delay));
        await EMAC.scanResourceLinks(resourceId);
        current++;
    }
    $('div#scan_message').empty();
    console.log('DONE!');
    return true;
}

EMAC.getRandomDelayTime = () => {
    var min = 200; // milliseconds
    var max = 1000; // milliseconds
    return Math.floor(Math.random() * (max - min) + min);
}