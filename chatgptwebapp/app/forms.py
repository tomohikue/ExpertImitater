"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))

class UploadFileForm(forms.Form):
    document_name = forms.CharField(max_length=300)
    description = forms.CharField(max_length=500)
    file = forms.FileField()

class UploadFileFormForCodeInterpriter(forms.Form):
    session_id = forms.CharField(max_length=100)
    file = forms.FileField()
    
class UploadFileFormForCodeInterpriterWithoutFile(forms.Form):
    session_id = forms.CharField(max_length=100)
    presetfile = forms.CharField(max_length=100)

    