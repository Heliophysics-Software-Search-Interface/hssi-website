var HSSI = HSSI || {};
HSSI.spinner = null;
HSSI.currentRequest = null;
HSSI.resourceFilterAnchor = null;

HSSI.handlePopState = function handlePopState (event) {
    if (event.state) {
        var  { url } = event.state;
        var params = url.substring(1).split('&'); 
        // reload the data based on historical URL
        // without adding a new entry to the browser history
        HSSI.loadContentByQueryParams(url, false).then(function() {
            // clearing all controls but do not collapse menus
            HSSI.clearAllFilterControls(false);
            if (params.length > 0) {
                if (params[0] !== 'all') {
                    // reset controls to previous states
                    params.forEach(qParam => {
                        var qPair = qParam.split('=');
                        switch (qPair[0]) {
                            case 'q':
                                $('#searchbar').val(qPair[1]);
                                HSSI.toggleSortVisible(false);
                                break;
                            case 'sort':
                                HSSI.setActiveSort(qPair[1]);
                                break;
                            case 'related_resource':
                                HSSI.toggleSortVisible(false);
                                break;
                            case 'category':
                            case 'tooltype':
                            case 'collection':
                                var filterId = qPair[1];
                                // check all boxes
                                $(`[name=${qPair[0]}_checkbox][value=${filterId}]`).prop('checked', true);
                                if ($(`form input[value=${filterId}]`).hasClass('parent_filter')) {
                                    // should be in "select all" state
                                    $(`.parent_filter[value=${filterId}]`).closest('li.filter_menu').addClass('selected_filter');
                                    $(`.parent_filter[value=${filterId}]`).closest('li.filter_menu').find('input.sub_filter').prop('checked', true);
                                }
                                break;
                            default:
                                break;
                        }
                    });
                }
                HSSI.determineSelectedUnselectedParents();
                HSSI.showResultCount(url);
                HSSI.showAppliedFilters(url);
            }
        });

    } else {
        // at the beginning of history, so just reload
        window.location.reload()
    }
}
// register pop state handler to handle back/forward button clicks
window.onpopstate = HSSI.handlePopState;

HSSI.buildFilterQueryParamsAndSend = function buildFilterQueryParamsAndSend() {
    // if we're in the mobile view, close the category
    // menu before loading new data
    if ($('.mobile-filter-toggle').is(':visible')) {
        if ($('.mobile-filter-toggle').parents('.mobile-filter-header').hasClass('expanded')) {
            $('.mobile-filter-toggle').click();
        }
    }
    
    var queryParams = [];

    var search_terms = document.getElementById("searchbar").value;
    if (search_terms) {
        queryParams.push(`q=${search_terms}`)
    }

    var selectedFilterIDs = [];
    var allSelectedFilters = $('div.filter-sidebar.hide-for-small-only input[type=checkbox]:checked');
    if (allSelectedFilters.length > 0) {
        $(allSelectedFilters).each(function() {
            if ($(this).hasClass('sub_filter')) {
                if (!$(this).closest('li.filter_menu').hasClass('selected_filter')) {
                    queryParams.push(`${$(this).attr('name').split('_')[0]}=${$(this).val()}`);
                    selectedFilterIDs.push($(this).val());
                }
            }  else {
                queryParams.push(`${$(this).attr('name').split('_')[0]}=${$(this).val()}`);
                selectedFilterIDs.push($(this).val());
            }
        })
    }

    // sort is irrelevant if search terms are present
    if (!search_terms) {
        // need to determine if filter parameters have changed or not
        var params = window.location.search.substring(1).split('&'); 
        var currentFilterIDs = params.filter(pair => {
            return pair.startsWith('category') || pair.startsWith('tooltype') || pair.startsWith('collection');
        }).map(pair => pair.split('=')[1]);
        var filtersChanged = false;
        if (selectedFilterIDs.length !== currentFilterIDs.length) {
            // definitely something changed
            filtersChanged = true;
        } else {
            var differences = selectedFilterIDs.filter(id => !currentFilterIDs.includes(id));
            filtersChanged = differences.length > 0;
        }
        // get the selected sort
        var sort = $('.sort-button.active-sort').attr('id').split('_')[2];
        queryParams.push(`sort=${sort}`);
    }

    var url = '?';
    if (queryParams.length > 0) {
        url += `${queryParams.join('&')}`;
    } else {
        url += 'all';
    }
    HSSI.loadContentByQueryParams(url, true);
}

HSSI.loadContentByQueryParams = function loadContentByQueryParams(queryParamUrl, addToHistory) {
    if (HSSI.currentRequest) {
        HSSI.currentRequest.abort();
        HSSI.currentRequest = null;
    }
    var dfd = $.Deferred();
    // need the content div as NOT a jQuery object for the spinny code
    var loader = document.getElementById('loading_modal');
    HSSI.spinner = HSSI.spinner || new Spin.Spinner();
    HSSI.spinner.spin(loader);
    $(loader).addClass('visible');
    HSSI.currentRequest = $.ajax({
        url: queryParamUrl,
        method: 'GET',
        dataType: 'json'
    }).done(function (response) {
        if (addToHistory) {
            window.history.pushState({ url: queryParamUrl }, '', queryParamUrl)
        }
        $('div#resource_content').html(response.resource_content);
        // re-init any dynamically loaded foundation content
        $('div#resource_content').foundation();
        HSSI.showResultCount(queryParamUrl);
        HSSI.showAppliedFilters(queryParamUrl);
        HSSI.scrollToContentTop();
    }).fail(function (xhr, status, error) {
        console.warn(status)
        console.warn(error)
        window.HSSIError = {
            xhr,
            status,
            error
        }
    }).always(function() {
        HSSI.currentRequest = null;
        $(loader).removeClass('visible');
        HSSI.spinner.stop();
        dfd.resolve();
    });
    return dfd.promise();
}

HSSI.determineSelectedUnselectedParents = function determineSelectedUnselectedParents() {
    var mainSections = $('div.filter_table');
    $(mainSections).each(function() {
        var parents = $(this).find('li.filter_menu');
        var hasSelectedParent = $(parents).toArray().some(el => $(el).hasClass('selected_filter'));
        var hasCheckedSubs = $(this).find('input.sub_filter:checked').length > 0;
        $(parents).each(function() {
            // don't do anything if it's a selected parent
            if (!$(this).hasClass('selected_filter')) {
                // not a selected parent
                if (hasSelectedParent || hasCheckedSubs) {
                    if ($(this).hasClass('is-accordion-submenu-parent')) {
                        var selectedSubs = $(this).find('input.sub_filter:checked');
                        if (selectedSubs.length > 0) {
                            // has selected sub items, should be "neutral"
                            $(this).removeClass('unselected_filter');
                        } else {
                            // might have had selected subs, but doesn't
                            $(this).addClass('unselected_filter');
                        }
                    } else {
                        // selected peer/parent or submenu with selections in main section, should be dimmed
                        $(this).addClass('unselected_filter');
                    }
                } else {
                    // no other selected peer/parent or checked subs in the main section,
                    // all should be neutral
                    $(this).removeClass('unselected_filter');
                }
            }
        });
    });
}

HSSI.handleParentFilterChange = function handleParentFilterChange() {
    if (this.name.startsWith('collection')) {
        // if a collection is being selected, clear all other filters
        // including other collection filters, to ensure that
        // only one collection can be selected at any time
        if (this.checked) {
            HSSI.clearSearchBox();
            HSSI.clearAllFilterCheckboxes(true, 'category');
            HSSI.clearAllFilterCheckboxes(true, 'tooltype');
            HSSI.clearAllFilterCheckboxes(true, 'collection');
            // reset this as checked
            $(this).prop('checked', true);
        } // proceed with default behavior
    } else {
        // if a category or tool type filter is being applied,
        // clear any collection filters
        HSSI.clearAllFilterCheckboxes(true, 'collection');
    }
    
    // sync checked state
    $(`[name=${this.name}][value=${this.value}]`).prop('checked', this.checked);
    // add or remove "selected" class from parent menu item
    if (this.checked) {
        $(`.parent_filter[value=${this.value}]`).closest('li.filter_menu').addClass('selected_filter').removeClass('unselected_filter');
    } else {
        $(`.parent_filter[value=${this.value}]`).closest('li.filter_menu').removeClass('selected_filter');
    }
    // check or uncheck all subcategories to match
    $(`.parent_filter[value=${this.value}]`).closest('li.filter_menu').find('input.sub_filter').prop('checked', this.checked);
    
    HSSI.determineSelectedUnselectedParents();
    HSSI.buildFilterQueryParamsAndSend();
}

HSSI.handleSubFilterChange = function handleSubFilterChange() {
    if (this.name.startsWith('collection')) {
        // if a collection is being selected, clear all other filters
        // including other collection filters, to ensure that
        // only one collection can be selected at any time
        if (this.checked) {
            HSSI.clearSearchBox();
            HSSI.clearAllFilterCheckboxes(true, 'category');
            HSSI.clearAllFilterCheckboxes(true, 'tooltype');
            HSSI.clearAllFilterCheckboxes(true, 'collection');
            // reset this as checked
            $(this).prop('checked', true);
        } // proceed with default behavior
    } else {
        // if a category or tool type filter is being applied,
        // clear any collection filters
        HSSI.clearAllFilterCheckboxes(true, 'collection');
    }

    // sync checked state
    var parentId = $(this).closest('li.filter_menu').find('input.parent_filter').attr('value');
    var thisId = `${parentId}_${this.value}`;
    $(`[name=${this.name}][id=${thisId}]`).prop('checked', this.checked);
    
    // find out if all siblings checked
    var siblings = $(this).closest('li.filter_menu').find('input.sub_filter');
    var checkedSibs = $(this).closest('li.filter_menu').find('input.sub_filter:checked');
    if ($(siblings).length > 1 && $(checkedSibs).length === $(siblings).length) {
        // select parent
        $(`.parent_filter[value=${parentId}]`).prop('checked', true);
        $(`.parent_filter[value=${parentId}]`).closest('li.filter_menu').addClass('selected_filter');
        // close the accordion
        $(this).closest('li.filter_menu').find('a.filter_dropdown').click()
    } else {
        // deselct parent
        $(`.parent_filter[value=${parentId}]`).prop('checked', false);
        $(`.parent_filter[value=${parentId}]`).closest('li.filter_menu').removeClass('selected_filter');
    }
    
    HSSI.determineSelectedUnselectedParents();
    HSSI.buildFilterQueryParamsAndSend();
}

HSSI.handleResourceLabelClick = function handleResourceLabelClick() {
    // set the scroll to anchor for when the data reloads
    var anchor = $(this).closest('div.callout.resource-info').prev('.anchor-name');
    HSSI.resourceFilterAnchor = $(anchor).attr('name');
    // figure out the filters to appy
    var resourceId = $(this).closest('div.callout.resource-info').data('resourceId');
    var parentIds = [];
    $(this).closest('.resource_info').find('input.resource_info_label').each(function(){
        parentIds.push(this.value);
    });
    var filterIds = [];
    parentIds.forEach(parentId => {
        var childList = $(`div.child-category-list[data-resource-id=${resourceId}]`).children(`[data-parent=${parentId}]`);
        if (childList.length > 0) {
            $(childList).each(function() {
                var childId = $(this).data('category');
                var inputId = `${parentId}_${childId}`;
                filterIds.push(inputId);
            });
        } else {
            filterIds.push(parentId);
        }
    });
    
    HSSI.clearAllFilterCheckboxes(true, 'tooltype');
    HSSI.clearAllFilterCheckboxes(true, 'collection');
    HSSI.clearAllFilterCheckboxes(false, 'category');

    filterIds.forEach(id => {
        var filter = $(`div#category-menu-main input[id=${id}]`);
        $(filter).prop('checked', true);
        // sync checked state
        $(`[name=${$(filter).attr('name')}][id=${id}]`).prop('checked', true);
        if (id.includes('_')) {
            // is child
            var parentId = id.split('_')[0];
            // find out if all siblings checked
            var siblings = $(filter).closest('li.filter_menu').find('input.sub_filter');
            var checkedSibs = $(filter).closest('li.filter_menu').find('input.sub_filter:checked');
            if ($(siblings).length > 1 && $(checkedSibs).length === $(siblings).length) {
                // select parent
                $(`.parent_filter[value=${parentId}]`).prop('checked', true);
                $(`.parent_filter[value=${parentId}]`).closest('li.filter_menu').addClass('selected_filter');
            } else {
                // deselct parent
                $(`.parent_filter[value=${parentId}]`).prop('checked', false);
                $(`.parent_filter[value=${parentId}]`).closest('li.filter_menu').removeClass('selected_filter');
            }

        } else {
            // is parent
            $(filter).closest('li.filter_menu').addClass('selected_filter').removeClass('unselected_filter');
            $(filter).closest('li.filter_menu').find('input.sub_filter').prop('checked', this.checked);
        }
    });
    HSSI.determineSelectedUnselectedParents();
    HSSI.buildFilterQueryParamsAndSend();
}

HSSI.setActiveSort = function setActiveSort(sortType) {
    // disable all, then set selected one active
    $('div#sort_menu .sort-button').removeAttr('selected').removeClass('active-sort');
    $(`div#sort_menu .sort-button[id$=${sortType}]`).attr('selected', 'true').addClass('active-sort');
}

HSSI.toggleSortVisible = function toggleSortVisible(visible) {
    if (visible) {
        $('div#sort_menu').show();
    } else {
        $('div#sort_menu').hide();
    }
}

HSSI.clearSearchBox = function clearSearchBox() {
    $("#searchbar").val('');
}

HSSI.submitSearch = function submitSearch() {
    // search results are sorted by relevance weight
    // so remove any applied sorting filters before submitting
    HSSI.setActiveSort('date');
    HSSI.toggleSortVisible(false);
    HSSI.buildFilterQueryParamsAndSend();
}

HSSI.clearAllFilterCheckboxes = function clearAllFilterCheckboxes(collapse, filterType) {
    var filterMenu = $(`div[id^=${filterType}-menu]`);
    $(filterMenu).find('[name$=_checkbox]').prop('checked', false);
    $(filterMenu).find('.selected_filter').removeClass('selected_filter');
    $(filterMenu).find('.unselected_filter').removeClass('unselected_filter');
    if (collapse) {
        $(filterMenu).find('li.filter_menu[aria-expanded=true]').find('a.filter_dropdown').click();
    }
    if (filterType === 'category') {
        $('div#resource_content').find('[name$=_checkbox]').prop('checked', false);
    }
}

HSSI.clearAllFilterControls = function clearAllFilterControls(collapseMenus) {
    HSSI.clearSearchBox();
    $('.filter-chip-container').empty();
    HSSI.clearAllFilterCheckboxes(collapseMenus, 'category');
    HSSI.clearAllFilterCheckboxes(collapseMenus, 'tooltype');
    HSSI.clearAllFilterCheckboxes(collapseMenus, 'collection');
    HSSI.setActiveSort('date');
    HSSI.toggleSortVisible(true);
}

HSSI.scrollToContentTop = function scrollToContentTop(delay) {
    // scroll to top of resource content box accounting for header menu row
    var stickyOffset = 40;
    if ($('.mobile-filter-toggle').is(':visible')) {
        stickyOffset = 170;
    }
    var sortTop = $('div.resource-content-header').offset().top - stickyOffset;
    if (delay && delay > 0) {
        setTimeout(function () {
            window.scrollTo(0, sortTop);
        }, delay);
    } else {
        window.scrollTo(0, sortTop);
    }
    // if there is an anchor set, scroll back to it
    if (HSSI.resourceFilterAnchor) {
        var scrollOffset = 140;
        if ($('.mobile-filter-toggle').is(':visible')) {
            scrollOffset += 265;
        }
        var anchorRelativeTop = $(`a.anchor-set[name=${HSSI.resourceFilterAnchor}]`).get(0).getBoundingClientRect().top;
        var resourceTop = $('div#resource_content').offset().top  + anchorRelativeTop - scrollOffset;
        window.scrollTo({ top: resourceTop, behavior: 'smooth' });
        HSSI.resourceFilterAnchor = null;
    }
}

HSSI.showResultCount = function showResultCount(queryParamUrl) {
    let results = $("#resource_content .callout").length;
    if (results === 0) {
        $('#result-count').html("No resources match your search...yet!<br/>Would you like to <a href='/submissions'>submit a new resource?</a>").show();
        $('#result-count').addClass('no-results');
        HSSI.toggleSortVisible(false);
    } else {
        var collections = $("#resource_content .callout.collection").length;
        var visibleResults = (results - collections);
        var resources = visibleResults === 1 ? 'resource' : 'resources';
        $('#result-count').removeClass('no-results');
        $('#result-count').html(`Showing ${visibleResults} published ${resources}. `);
        var params = queryParamUrl.substring(1).split('&');
        if (params.some(param => param.startsWith('category=')
                                  || param.startsWith('q=')
                                  || param.startsWith('collection='))
                && visibleResults > 0) {
            var exportLink = $('<a>(Download results)</a>');
            exportLink.attr('href', `/export${window.location.search}`);
            exportLink.attr('target', '_blank');
            $('#result-count').append(exportLink);
        }
        if (params.some(param => param.startsWith('related_resource=')
                                  || param.startsWith('q='))) {
            HSSI.toggleSortVisible(false);
        } else {
            HSSI.toggleSortVisible(true);
        }
    }
}

HSSI.showAppliedFilters = function showAppliedFilters(queryParamUrl) {
    $('.filter-chip-container').empty();
    var params = queryParamUrl.substring(1).split('&');
    var filterTypes = [...new Set(params.map(param => param.split('=')[0]))];
    var filters = filterTypes.map(type => {
        ids = params.filter(param => param.startsWith(type)).map(param => param.split('=')[1]);
        return {
            type,
            ids
        };
    });
    filters.forEach(filter => {
        switch (filter.type) {
            case 'category':
            case 'tooltype':
            case 'collection':
                HSSI.addFilterChipSection(filter);
                break;
            default:
                break;
        }
    });
}

HSSI.getFilterLabel = function getFilterLabel(filterId) {
    var label = $(`label[for$=${filterId}]`)[0];
    var labelText = $(label).text();
    return labelText;
}

HSSI.getParentClass = function getParentClass(filterId) {
    var label = $(`label[for$=${filterId}]`)[0];
    var className = $(label).attr('parent-abbr');
    return className;
}

HSSI.addFilterChip = function addFilterChip(filterId) {
    var label = HSSI.getFilterLabel(filterId);
    var className = HSSI.getParentClass(filterId);
    $(`div.filter-chip-container`).append(`<div class="filter-chip ${className}" filter-id="${filterId}"><span>${label}</span><i class="fi-x"></i></div>`);
}

HSSI.addFilterChipSection = function addFilterChipSection(filter) {
    var section = $('<div class="filter-chip-section"></div>');
    filter.ids.forEach(filterId => {
        var label = HSSI.getFilterLabel(filterId);
        var className = HSSI.getParentClass(filterId);
        $(section).append(`<div class="filter-chip ${className}" filter-id="${filterId}"><span>${label}</span><i class="fi-x"></i></div>`);
    });
    $('div.filter-chip-container').append(section);
}

$(document).ready(function () {

    //// HOOK UP EVENT HANDLERS

    // sort buttons
    $('div#sort_menu .sort-button').on('click', function() {
        if ($(this).attr('selected')) {
            // is already the selected sort method, no change
            return;
        }
        var sortType = $(this).attr('id').split('_')[2];
        HSSI.setActiveSort(sortType);
        HSSI.buildFilterQueryParamsAndSend();
    });

    // search button
    $('button.search-button').on('click', function() {
        HSSI.submitSearch();
    });

    // seach textbox
    $('input#searchbar').on('keyup', function(evt) {
        if (evt.originalEvent.key === 'Enter' || evt.originalEvent.keyCode === 13) {
            HSSI.submitSearch();
        }
    });

    // prevent accordion menu expansion when
    // clicking on a parent filter name to select it
    $('div.filter_label label').on('click', function(evt) {
        evt.stopPropagation();
    });

    // regular reset button
    $('input.reset.button').on('click', function(evt) {
        // if in moble view stop propagation because
        // we manually close the menu in buildFilterQueryParamsAndSend
        if ($('.mobile-filter-toggle').is(':visible')) {
            evt.originalEvent.stopPropagation();
        }
        HSSI.clearAllFilterControls(true);
        HSSI.buildFilterQueryParamsAndSend();
    });

    // parent filters
    $('.parent_filter[name$=_checkbox]').on('change', HSSI.handleParentFilterChange);

    // sub filters
    $('.sub_filter[name$=_checkbox]').on('change', HSSI.handleSubFilterChange);

    // resource info label boxes
    $('div#resource_content').on('change','.resource_info_label[name=category_checkbox]', HSSI.handleResourceLabelClick);

    // related resource buttons
    $('div#resource_content').on('click', 'a.related_btn', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        // hide the foundation tooltip to prevent bizarre offset bug
        $(this).foundation('hide');
        var queryParamUrl = $(this).attr('href');
        HSSI.clearAllFilterControls(true);
        HSSI.toggleSortVisible(false);
        HSSI.loadContentByQueryParams(queryParamUrl, true);
    });

    // highlighted resource "reset" button
    $('div#resource_content').on('click', 'a.reset_btn', function(evt) {
        evt.originalEvent.preventDefault();
        HSSI.clearAllFilterControls(true);
        HSSI.buildFilterQueryParamsAndSend();
    });

    // copy link icon
    $('div#resource_content').on('click', '.icon-container>.copy_img', function () {
        var tempElement = $("<input>");
        $("body").append(tempElement);
        tempElement.val($(this).closest(".icon-container").find("span.copy_link").text()).select();
        document.execCommand("Copy");
        alert("Link copied!")
        tempElement.remove();
    });

    // filter chips
    $('div.filter-chip-container').on('click', 'div.filter-chip>i', function() {
        var filterId = $(this).parent('.filter-chip').attr('filter-id');
        // find the single filter checkbox within this
        // same filter menu structure so we only trigger "change"
        // on one checkbox (simulating an actual UI click)
        var filterCheckbox = $(this).closest('div.filter_selector').find(`input[value=${filterId}]`);
        $(filterCheckbox).prop('checked', false);
        $(filterCheckbox).trigger('change');
        // delete the filter chip itself
        $(this).parent('.filter-chip').remove();
    });

    // main filter sections
    $('.filter-tab').click(function() {
        if ($(this).hasClass('open')) {
            return;
        } else {
            var idx = $(this).index();
            $(this).closest('.filter-tab-container').find('.filter-tab.open').removeClass('open');
            $(this).closest('.filter-tab-container').next('.filter-menus').find('.filter-section-body.open').removeClass('open');
            $(this).addClass('open');
            var menuSection = $(this).closest('.filter-tab-container').next('.filter-menus').find('.filter-section-body').get(idx);
            $(menuSection).addClass('open');
        }
    });

    // mobile menu slide toggle
    $('.mobile-filter-toggle').click(function() {
        var container = $(this).parents(".mobile-filter-header");
        var mobile_menu_container = container.find(".mobile-menu-container");
        var trigger = container.find(".category-t");

        mobile_menu_container.slideToggle(200);

        if (trigger.hasClass("category-o")) {
            trigger.removeClass("category-o");
        } else {
            trigger.addClass("category-o");
        }

        if (container.hasClass("expanded")) {
            container.removeClass("expanded");
        } else {
            container.addClass("expanded");
        }
    });

    // expand resource info arrow
    $('div#resource_content').on('click', 'div.arrow', function() {
        $(this).toggleClass('active');
        $(this).find('.rotate').toggleClass('down');
        $(this).closest('div.resource-info').toggleClass('collapsed');
    });

    // credit links
    $('div#resource_content').on('click', 'p.resource_info > a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var resource_id = $(this).closest('div.resource-info').data('resource-id');
        getOutboundLink($(this).attr('href'), 'resource_credits_link', resource_id, null);
    });

    // any links in the description body
    $('div#resource_content').on('click', '.resource_description > a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var resource_id = $(this).closest('div.resource-info').data('resource-id');
        getOutboundLink($(this).attr('href'), 'resource_description_link', resource_id, null);
    });

    // any links in the collection description
    $('div#resource_content').on('click', 'div.collection-description > a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var collection_id = $(this).closest('div.resource-info').data('collection-id');
        var collection_name = $(this).closest('div.resource-info').find('div.collection-header').text();
        collection_name = collection_name.trim().split(' ');
        collection_name.shift();
        collection_name.pop();
        collection_name = collection_name.join(' ');
        getOutboundLink($(this).attr('href'), 'collection_description_link', null, null, { collection_id, collection_name });
    });

    // any links in the collection curators
    $('div#resource_content').on('click', 'div.collection-curators > a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var curator_name = $(this).text();
        getOutboundLink($(this).attr('href'), 'collection_curator_link', null, null, { curator_name });
    });

    // build badge link HTML and markdown for modal
    $('div#resource_content').on('click', 'div.citation_id > svg', function(evt) {
        var HSSILink = $(this).closest('.icon-container').find('span.copy_link').text();
        var svgText = $(this).find('title').text();
        var parts = svgText.split(':');
        var badgeSrc = `https://img.shields.io/badge/HSSI-${parts[1].trim().replace('-', '--')}-blue`;
        var HSSIAlt = `HSSI ${parts[1].trim()}`;
        var htmlToEncode = `<a href="${HSSILink}"><img src="${badgeSrc}" alt="${HSSIAlt}"></a>`;
        htmlToEncode = htmlToEncode.replace(/</g, '&lt;');
        htmlToEncode = htmlToEncode.replace(/>/g, '&gt;');
        var htmlString = '<div><div class="badge-dialog-title">HSSI Badge</div>';
        htmlString += '<div class="badge-label">HTML <i class="fa fa-files-o copy-markup-icon" title="Copy"></i> <span class="copy-message">Copied!</span></div>';
        htmlString += `<textarea class='badge-markup' readonly>${htmlToEncode}</textarea>`;
        htmlString += '<div class="badge-label">Markdown <i class="fa fa-files-o copy-markup-icon" title="Copy"></i> <span class="copy-message">Copied!</span></div>';
        htmlString += `<textarea class='badge-markup' readonly>[![HSSI](${badgeSrc})](${HSSILink})</textarea>`;
        htmlString += '<div class="badge-label">Image URL <i class="fa fa-files-o copy-markup-icon" title="Copy"></i> <span class="copy-message">Copied!</span></div>';
        htmlString += `<textarea class='badge-markup' readonly>${badgeSrc}</textarea>`;
        htmlString += '<div class="badge-label">Target URL <i class="fa fa-files-o copy-markup-icon" title="Copy"></i> <span class="copy-message">Copied!</span></div>';
        htmlString += `<textarea class='badge-markup' readonly>${HSSILink}</textarea>`;
        htmlString += `</div>`;
        $('#modal .modal-content').html(htmlString);
        if ($('#modal .modal-content').hasClass('popup-title')) {
            $('#modal .modal-content').removeClass('popup-title');
        }
        $('#modal').foundation('open');
    });

    $('#modal .modal-content').on('click', 'i.copy-markup-icon', function() {
        var copyText = $(this).closest('.badge-label').next('.badge-markup').text();
        var copyMessage = $(this).next('.copy-message');
        if (navigator.clipboard) {
            navigator.clipboard.writeText(copyText).then(function() {
                $(copyMessage).show().fadeOut(1500);
            }, function(err) {
                alert('Sorry, your browser does not support the Clipboard API. You can manually copy the text by selecting it in the text box.');
            });
        } else {
            alert('Sorry, your browser does not support the Clipboard API. You can manually copy the text by selecting it in the text box.');
        }
    });

    // category/collection descriptions modal
    $('div.cat-description').on('click', function(evt) {
        evt.originalEvent.preventDefault();
        $(`#${$(this).attr('data-description-type')}-description-modal`).foundation('open');
    });

    // category/collection description modal links
    $('div.description-modal.reveal').on('click', 'div.cat-curators a', function(evt) {
        // stop the regular <a> click
        evt.originalEvent.preventDefault();
        var modal_id = $(this).closest('div.description-modal').attr('id');
        var type = `${modal_id.split('-')[0]}_curator_link`;
        var curator_name = $(this).text();
        getOutboundLink($(this).attr('href'), type, null, null, { curator_name });
    })

    //// REGULAR PAGE LOAD ACTIONS
    ////
    //// this is where we handle actions we need to take
    //// if the initial page load has any special filter
    //// or sort settings applied, i.e. someone bookmarked
    //// the url with query params present

    if (window.location.search) {
        var params = window.location.search.substring(1).split('&');
        if (params.length > 0 && params[0] !== 'all') {
            if (params.some(param => param.startsWith('category=')
                                    || param.startsWith('tooltype=')
                                    || param.startsWith('collection='))) {
                // at least one filter was checked, so look for selected parent filters and
                // "fake" check their children to visually represent "all selected"
                $('.menu input.parent_filter:checked').each(function () {
                    $(this).closest('li.filter_menu').find('input.sub_filter').prop('checked', true);
                });
                // if the preselected filter was for collection,
                // need to make sure the collection tab is showing
                if (params.some(param => param.startsWith('collection='))) {
                    $('.filter-tab:contains("Collections")').click();
                }
            }
            var sortParam = params.find(param => param.startsWith('sort='));
            if (sortParam && sortParam.split('=')[1] == 'name') {
                HSSI.setActiveSort('name');
            }
            // template rendering handles search box value based on "q" param
            // so we just need to know if it's there
            if (params.some(param => param.startsWith('related_resource=')
                                  || param.startsWith('q='))) {
                HSSI.toggleSortVisible(false);
            }
            // if the initial load already has settings/params on the URL,
            // assume the person has visited before and go straight
            // to the content (need slight delay for some reason)
            HSSI.scrollToContentTop(200);
        }
    }
    HSSI.showResultCount(window.location.search);
    HSSI.showAppliedFilters(window.location.search);
});