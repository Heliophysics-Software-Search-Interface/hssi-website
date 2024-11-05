from django.forms import HiddenInput, ModelForm
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Feedback, Subscription
import uuid


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

class AnalyticsForm(forms.Form):
    # remake_all = forms.BooleanField(label='Remake all plots', initial=True, required=False)
    remake_all = forms.CharField(required=False)
    # clicks_per_tool = forms.BooleanField(label='External Unique Clicks per Tool', initial=False, required=False)
    # visits_over_time = forms.BooleanField(label='External Sessions over Time', initial=False, required=False)
    # weekly_visits = forms.BooleanField(label='External Sessions by Week', initial=False, required=False)
    # exit_clicks_by_category = forms.BooleanField(label='External Unique Clicks per Category', initial=False, required=False)
    # twitter_analytics = forms.BooleanField(label='Twitter Analytics', initial=False, required=False)
    # social_traffic = forms.BooleanField(label='Social media traffic', initial=False, required=False)
    # RSS_report = forms.BooleanField(label='RSS views', initial=False, required=False)
    # youtube_analytics = forms.BooleanField(label='youtube_analytics', initial=False, required=False)
    # tools_per_category = forms.BooleanField(label='Number of tools per category', initial=False, required=False)
    # tools_per_coding_language = forms.BooleanField(label='Number of tools per coding language', initial=False, required=False)
    # new_visitors_over_time = forms.BooleanField(label='Number of new visitors over time', initial=False, required=False)
    # n_tools = forms.BooleanField(label='Number of tools', initial=False, required=False)
    # new_user_fraction = forms.BooleanField(label='External Fraction of Sessions from New Users', initial=False, required=False)



# class SubscriptionForm(ModelForm):
#     print("====== in forms.py")
#     class Meta:
#         model = Subscription
#         fields = [
#             'email_address', 'categories', 'daily_digest'
#         ]
#         # widgets = {
#         #     'resource_id_temp': HiddenInput()
#         # }
#
#     def clean_id(self):
#
#         subscription_id = self.cleaned_data['id']
#         print(f"===============subscription id {subscription_id}")
#         if subscription_id is None:  # If this is a new Submission, not an edit ...
#             subscription_id = uuid.uuid4()
#             print(f"===============new subscription id {subscription_id}")
#         return subscription_id
#
#     def __init__(self, *args, **kwargs):
#         super(SubscriptionForm, self).__init__(*args, **kwargs)
#
#         self.helper = FormHelper()
#         self.helper.form_id = 'resource_subscription_form'
#         self.helper.add_input(Submit('submit', 'Submit', css_class='hollow button', onclick="submitResourceFeedback()"))
