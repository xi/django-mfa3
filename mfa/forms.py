from django import forms
from django.utils.translation import gettext_lazy as _


class MFAAuthForm(forms.Form):
    code = forms.CharField(label=_('Authentication code'))

    def clean(self):
        cleaned_data = super().clean()
        try:
            cleaned_data['secret'] = self.complete(cleaned_data['code'])
        except ValueError as e:
            raise forms.ValidationError(_('Validation failed')) from e
        return cleaned_data


class MFACreateForm(MFAAuthForm):
    name = forms.CharField(label=_('Name'), max_length=32)