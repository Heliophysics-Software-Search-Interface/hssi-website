var HSSI = HSSI || {};
HSSI.spinner = null;
HSSI.currentRequest = null;
HSSI.resourceFilterAnchor = null;

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
		// re-render any TeX math content
		if (window.MathJax) {
			MathJax.typeset();
		}
		HSSI.showResultCount(queryParamUrl);
		HSSI.showAppliedFilters(queryParamUrl);
		HSSI.scrollToContentTop();
	}).fail(function (xhr, status, error) {
		console.warn(status)
		console.warn(error)
		window.mySiteError = {
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
	
	HSSI.clearAllFilterCheckboxes(false, 'tooltype');
	HSSI.clearAllFilterCheckboxes(false, 'collection');
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
	
}

/** @param {string} queryParamUrl */
HSSI.showAppliedFilters = function(queryParamUrl) {
	const filterChipContainer = document.querySelector('filter-chip-container');
	const params = queryParamUrl.substring(1).split('&');
	const filterTypes = [
		...new Set(params.map(param=>param.split('=')[0].replace('_not','')))
	];
	const filters = filterTypes.map(type => {
		const infos = (params
			.filter(param => param.startsWith(type))
			.map(param => {
				const splitParam = param.split('=');
				return {
					negated: splitParam[0].endsWith('_not'),
					id: splitParam[1]
				}
			})
		);
		return {
			type,
			ids: infos.map(info=>info.id),
			index_negated: infos.map(info=>info.negated)
		}
	});
	for(const filter of filters) {
		if (['category', 'tooltype', 'collection'].includes(filter.type))
			HSSI.addFilterChipSection(filter)
	}
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

/**
 * @typedef {Object} FilterInfo
 * @property {string} type the filter type
 * @property {Array<string>} ids the uids of the tags in the filter
 * @property {Array<bool>} index_negated whether the id at each index is negated
 * @param {FilterInfo} filter 
 */
HSSI.addFilterChipSection = function addFilterChipSection(filter) {
	const containers = document.querySelectorAll('div.filter-chip-container');
	const section = document.createElement('div');
	section.classList.add('filter-chip-section');
	for(const i in filter.ids){
		const id = filter.ids[i];
		const negated = filter.index_negated[i];
		
		const filterChip = document.createElement('div');
		filterChip.setAttribute('filter-id', id);
		filterChip.classList.add("filter-chip", HSSI.getParentClass(id));
		if(negated) filterChip.classList.add('negated');
		
		const filterChipLabel = document.createElement('span');
		filterChipLabel.innerText = HSSI.getFilterLabel(id);

		const deleteChipButton = document.createElement('i');
		deleteChipButton.classList.add('fi-x');

		filterChip.append(filterChipLabel, deleteChipButton);
		section.appendChild(filterChip);
	}
	for(container of containers) container.appendChild(section);
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
	$('div#resource_content').on('change','.resource_info_label[name=tooltype_checkbox]', HSSI.handleResourceLabelClick);

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

	// filter chip remove
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
	
	// filter chip negation
	$('div.filter-chip-container').on('click', 'div.filter-chip>span', function(e) {
		/** @type {HTMLSpanElement} */
		
		// get element and filter id
		let span = this;
		const filterID = span.parentElement.getAttribute('filter-id');
		
		// find out if current query param is negated or not
		let params = new URLSearchParams(window.location.search);
		let negated = false;
		for (let pair of params.entries()) {
			if (pair[1] == filterID) {
				negated = pair[0].endsWith('_not');
				break;
			}
		}
		negated = !negated;

		// toggle negation style
		if(negated) span.parentElement.classList.add("negated");
		else span.parentElement.classList.remove("negated");
		
		// negate query params
		let new_pairs = [];
		for (let pair of params.entries()) {
			if (pair[1] == filterID) {
				if(negated){
					new_pairs.push([
						pair[0] + "_not", 
						pair[1]
					]);
				}
				else {
					new_pairs.push([
						pair[0].replace("_not", ""),
						pair[1]
					]);  
				}
				console.log(new_pairs[new_pairs.length - 1]);
				params.delete(pair[0], pair[1]);
			}
		}
		for (let pair of new_pairs) {
			params.append(pair[0], pair[1]);
		}

		console.log(params.toString().split('&'));

		// apply new query
		window.location.search = params.toString();
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
});