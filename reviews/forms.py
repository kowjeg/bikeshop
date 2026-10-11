from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comments']
        labels = {
            'rating': 'Оценка',
            'comments': 'Комментарий',
        }
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(5, 0, -1)]),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Что понравилось, что нет?'}),
        }