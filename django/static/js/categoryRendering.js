	function rerenderCategoriesHierarchically(category_hierarchy_json, category_names_by_id_json, selected_category_ids_json)
	{
		var category_hierarchy = JSON.parse(category_hierarchy_json);
		var category_names_by_id = JSON.parse(category_names_by_id_json);
		var selected_category_ids = [];

		if (selected_category_ids_json && selected_category_ids_json.length > 0)
		{
			selected_category_ids = JSON.parse(selected_category_ids_json);
		}

		var hint = document.getElementById("hint_id_categories").outerHTML;
		var categoriesHTML = '<label class="control-label">Categories (check all that apply)</label>'
		var count = 0;

		for (category_id in category_hierarchy)
		{
			categoriesHTML += '<div class="category"><label for="id_categories_' + ++count + '">' 
			categoriesHTML += '<input type="checkbox" id="id_categories_' + count + '" value="' + category_id + '" name="categories"';

			if (selected_category_ids.includes(category_id))
			{
				categoriesHTML += ' checked'
			}
				
			categoriesHTML += '>' + category_names_by_id[category_id] + '</label>';
		
			var subcategories = category_hierarchy[category_id]

			for (var subcount = 0; subcount < subcategories.length;)
			{
				var subcategory_id = subcategories[subcount];
				categoriesHTML += '<div class="subcategory"><label class="checkbox" for="id_categories_' + count + '.' + ++subcount + '">'
				categoriesHTML += '<input type="checkbox" id="id_categories_' + count + '.' + subcount + '" value="' + subcategory_id + '" name="categories"';

				if (selected_category_ids_json.includes(subcategory_id))
				{
					categoriesHTML += ' checked'
				}
					 
				categoriesHTML += '>' + category_names_by_id[subcategory_id] + '</label></div>';
			}

			categoriesHTML += '</div>';
		}

		categoriesHTML += hint;
		
		var category_selection_element = document.getElementById("div_id_categories");
		category_selection_element.innerHTML = categoriesHTML;
	}
