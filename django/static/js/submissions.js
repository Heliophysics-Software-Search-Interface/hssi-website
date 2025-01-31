var unsaved = false;

function unloadPage(){ 
    if(unsaved){
        return "You have unsaved changes on this page. Do you want to leave this page and discard your changes or stay on this page?";
    }
}

window.onbeforeunload = unloadPage;

$(document)._submit = $(document).submit; 
$(document).on("submit", function () {
    window.onbeforeunload = null;
    this._submit();
});

$(document).ready(function() {
    $(":input").change(function(){ //triggers change in all input fields including text type
        unsaved = true;
    });
    
    $("#div_id_private_code_or_data_link").hide();
    $(".checkboxinput").change(function() {
        if(this.checked) {
            $("#div_id_private_code_or_data_link").show(300);
        } else {
            $("#div_id_private_code_or_data_link").hide(300);
        }
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

     var divIDsToMove = {
        'resource-details': [
            'div_id_subtitle',
            'div_id_version',
            'div_id_search_keywords',
            'div_id_code_languages',
            'div_id_ascl_id',
            'div_id_logo_image',
            'div_id_logo_link',
            'div_id_related_tool_string',
            'div_id_host_app_on_hssi',
            'div_id_host_data_on_hssi',
            'div_id_private_code_or_data_link',
            'div_id_submission_notes'
        ],
        'science-categories': [
            'div_id_categories',
            'div_id_other_category'
        ],
        'resource-links': [
            'div_id_about_link',
            'div_id_ads_abstract_link',
            'div_id_download_link',
            'div_id_download_data_link',
            'div_id_jupyter_link',
            'div_id_launch_link',
            'div_id_demo_link',
        ]
     };

     var resourceDetails = $('<div class="resource-details hidden-fields"></div>').insertBefore('form#id-submission_form div.form-actions');
     var scienceCategories = $('<div class="science-categories hidden-fields"></div>').insertBefore('form#id-submission_form div.form-actions');
     var resourceLinks = $('<div class="resource-links hidden-fields"></div>').insertBefore('form#id-submission_form div.form-actions');

     var keys = Object.keys(divIDsToMove);
     keys.forEach(key => {
        var container = $(`div.${key}`);
        divIDsToMove[key].forEach(divId => {
            $(`div#${divId}`).detach().appendTo(container);
        })
     });

     $('<div class="expand-additional"><a class="expand-additional"><div class="expand-arrow"></div><div class="expand-text"><div>Provide Additional Resource Details</div><div>(click to expand)</div></div></a></div>').insertBefore(resourceDetails);
     $(resourceDetails).hide();

     $('<div class="expand-additional"><a class="expand-additional"><div class="expand-arrow"></div><div class="expand-text"><div>Select Resource\'s Science Categories</div><div>(click to expand)</div></div></a></div>').insertBefore(scienceCategories);
     $(scienceCategories).hide();

     $('<div class="expand-additional"><a class="expand-additional"><div class="expand-arrow"></div><div class="expand-text"><div>Provide Resource Related Web Links</div><div>(click to expand)</div></div></a></div>').insertBefore(resourceLinks);
     $(resourceLinks).hide();

     $('a.expand-additional').click(function() {
        if ($(this).hasClass('open')) {
            $(this).removeClass('open');
            $(this).closest('div.expand-additional').next('div.hidden-fields').hide(300);
        } else {
            $(this).addClass('open');
            $(this).closest('div.expand-additional').next('div.hidden-fields').show(300);
        }
     });
});
