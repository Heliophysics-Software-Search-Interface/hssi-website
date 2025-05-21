from ...models import people
from .model_object_selector import ModelObjectSelector

class PeopleSelector(ModelObjectSelector):
    """ A selector widget that allows user to select person object in the db """
    
    template_name: str = 'widgets/model_object_selector.html'

    multi_select = True
    case_sensitive_filtering = False
    filter_on_focus = False
    dropdown_button = False
    dropdown_on_focus = False
    dropdown_on_blank = False
    new_object_field = None

