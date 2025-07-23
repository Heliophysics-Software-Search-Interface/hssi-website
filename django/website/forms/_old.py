from django.forms import HiddenInput, ModelForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from ..models import Feedback


class FeedbackForm(ModelForm):

	class Meta:
		model = Feedback
		fields = [
			'resource_id_temp', 'provide_demo_video', 'provide_tutorial', 'provide_web_app', 'relate_a_resource', 'correction_needed', 'comments'
		]
		widgets = {
			'resource_id_temp': HiddenInput()
		}

	def __init__(self, *args, **kwargs):
		super(FeedbackForm, self).__init__(*args, **kwargs)

		self.helper = FormHelper()
		self.helper.form_id = 'resource_feedback_form'
		self.helper.add_input(Submit('submit', 'Submit', css_class='hollow button', onclick="submitResourceFeedback()"))
