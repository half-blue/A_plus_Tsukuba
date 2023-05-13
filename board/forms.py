from django import forms
from .models import Review, Tag

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ['ratings_overall', 'ratings_easiness', 'ratings_content', 'comment', 'tags']
        widgets = { 
            'ratings_easiness': forms.TextInput(attrs={'type': 'range'}),
            'ratings_content': forms.TextInput(attrs={'type': 'range'}),
            'tags': forms.CheckboxSelectMultiple(),
        }
    
    # バリデーションエラーがある場合は、エラーを表示する
    def clean_comment(self):
        comment = self.cleaned_data['comment'].strip()
        if len(comment) < 2:
            raise forms.ValidationError('コメントが短すぎます')
        return comment
