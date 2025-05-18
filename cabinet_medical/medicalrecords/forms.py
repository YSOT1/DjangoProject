from django import forms
from .models import DoctorRating

class DoctorRatingForm(forms.ModelForm):
    """Form for submitting doctor ratings."""
    class Meta:
        model = DoctorRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your experience with this doctor...'})
        } 