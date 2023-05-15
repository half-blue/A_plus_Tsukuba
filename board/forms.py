from django import forms
from .models import Review

class Bs5ButtonCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = 'widgets/bs5_button_checkbox_select.html'
    option_template_name = 'widgets/bs5_button_checkbox_select_option.html'

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ['ratings_overall', 'ratings_easiness', 'ratings_content', 'comment', 'tags']
        widgets = { 
            'ratings_easiness': forms.TextInput(attrs={'type': 'range'}),
            'ratings_content': forms.TextInput(attrs={'type': 'range'}),
            'tags': Bs5ButtonCheckboxSelectMultiple()
        }
