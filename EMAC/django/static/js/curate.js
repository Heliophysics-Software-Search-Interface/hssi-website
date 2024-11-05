var hasChanges = false;

function unloadPage(){ 
    if(hasChanges){
        return "You have unsaved changes on this page. Do you want to leave this page and discard your changes or stay on this page?";
    }
}

window.onbeforeunload = unloadPage;

$(document).on("submit", function (evt) {
    window.onbeforeunload = null;
    var shouldSave = hasChanges;
    if (!hasChanges) {
        shouldSave = confirm("No changes were suggested in the Curation form — would you still like to mark this resource as 'Curated'?");
    }
    if (shouldSave) {
        return true;
    } else {
        window.onbeforeunload = unloadPage;
        evt.preventDefault();
        return false;
    }
});

$(document).ready(function() {
    // re-render checkboxes to show hierarchy
    // whether or not the form is locked
    rerenderCategoriesHierarchically(JSON.stringify(categoryHierarchy), JSON.stringify(categoryNamesByID), JSON.stringify(selectedCategoryIDs));
    rerenderCollectionsHierarchically(JSON.stringify(collectionHierarchy), JSON.stringify(collectionNamesByID), JSON.stringify(selectedCollectionIDs));

    // set up the accordions
    var divIDsToMove = {
        'science-categories': ['div_id_categories'],
        'collections': ['div_id_collections']
    }

    var scienceCategories = $('<div class="science-categories hidden-fields"></div>').insertBefore('form#id-submission_form div.form-actions');
    var collections = $('<div class="collections hidden-fields"></div>').insertBefore('form#id-submission_form div.form-actions');

    var keys = Object.keys(divIDsToMove);
    keys.forEach(key => {
       var container = $(`div.${key}`);
       divIDsToMove[key].forEach(divId => {
           $(`div#${divId}`).detach().appendTo(container);
       })
    });

    $('<div class="expand-additional"><a class="expand-additional"><div class="expand-arrow"></div><div class="expand-text"><div>Science Categories</div><div>(click to expand)</div></div></a></div>').insertBefore(scienceCategories);
     $(scienceCategories).hide();

     $('<div class="expand-additional"><a class="expand-additional"><div class="expand-arrow"></div><div class="expand-text"><div>Collections</div><div>(click to expand)</div></div></a></div>').insertBefore(collections);
     $(collections).hide();

     $('a.expand-additional').click(function() {
        if ($(this).hasClass('open')) {
            $(this).removeClass('open');
            $(this).closest('div.expand-additional').next('div.hidden-fields').hide(300);
        } else {
            $(this).addClass('open');
            $(this).closest('div.expand-additional').next('div.hidden-fields').show(300);
        }
     });


     // handle locked/unlocked state
    if (locked) {
        // if the form is locked, disable all text inputs and checkboxes
        $('#id-submission_form input[type=text]').each(function() {
            $(this).prop('disabled', true);
        });
        $('#id-submission_form input[type=checkbox]').each(function() {
            $(this).prop('disabled', true);
        });
    } else {
        // if the form is not locked, wire up all the change handlers

        $(":input").change(function(){ //triggers change in all input fields including text type
            hasChanges = true;
        });

        $("input[name='categories']").change(function() {
            if (this.checked) {
                if ($(this).closest("div").hasClass("subcategory")){
                    category_checkbox_selector = "#" + $(this).attr("id").substr(0, $(this).attr("id").indexOf("."));
                    $(category_checkbox_selector).prop("checked", true);
                }
            }
            else if ($(this).closest("div").hasClass("category")){
                $(this).closest("div").find("input[type='checkbox']").prop('checked', false);
            }
         });
    
         $("input[name='collections']").change(function() {
            if (this.checked) {
                if ($(this).closest("div").hasClass("subcollection")) {
                    var collection_checkbox_selector = "#" + $(this).attr("id").substr(0, $(this).attr("id").indexOf("."));
                    $(collection_checkbox_selector).prop("checked", true);
                }
            }
            else if ($(this).closest("div").hasClass("collection")) {
                $(this).closest("div").find("input[type='checkbox']").prop('checked', false);
            }
         });
    }
});
