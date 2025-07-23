function rerenderCollectionsHierarchically(collection_hierarchy_json, collection_names_by_id_json, selected_collection_ids_json) {
	var collection_hierarchy = JSON.parse(collection_hierarchy_json);
	var collection_names_by_id = JSON.parse(collection_names_by_id_json);
	var selected_collection_ids = [];

	if (selected_collection_ids_json && selected_collection_ids_json.length > 0) {
		selected_collection_ids = JSON.parse(selected_collection_ids_json);
	}

	var hint = document.getElementById("hint_id_collections").outerHTML;
	var collectionsHTML = '<label class="control-label">Collections (check all that apply)</label>'
	var count = 0;

	for (var collection_id in collection_hierarchy) {
		collectionsHTML += '<div class="collection"><label for="id_collections_' + ++count + '">' 
		collectionsHTML += '<input type="checkbox" id="id_collections_' + count + '" value="' + collection_id + '" name="collections"';

		if (selected_collection_ids.includes(collection_id)) {
			collectionsHTML += ' checked'
		}
			
		collectionsHTML += '>' + collection_names_by_id[collection_id] + '</label>';
	
		var subcollections = collection_hierarchy[collection_id]

		for (var subcount = 0; subcount < subcollections.length;) {
			var subcollection_id = subcollections[subcount];
			collectionsHTML += '<div class="subcollection"><label class="checkbox" for="id_collections_' + count + '.' + ++subcount + '">'
			collectionsHTML += '<input type="checkbox" id="id_collections_' + count + '.' + subcount + '" value="' + subcollection_id + '" name="collections"';

			if (selected_collection_ids_json.includes(subcollection_id)) {
				collectionsHTML += ' checked'
			}
				 
			collectionsHTML += '>' + collection_names_by_id[subcollection_id] + '</label></div>';
		}

		collectionsHTML += '</div>';
	}

	collectionsHTML += hint;
	
	var category_selection_element = document.getElementById("div_id_collections");
	category_selection_element.innerHTML = collectionsHTML;
}
