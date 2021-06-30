from django import forms
from django.utils.translation import gettext_lazy as _


class MFAAuthForm(forms.Form):
    code = forms.CharField(label=_('Authentication code'))

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        if code:
            try:
                cleaned_data['secret'] = self.complete(code)
            except ValueError as e:
                raise forms.ValidationError(_('Validation failed')) from e
        return cleaned_data


class MFACreateForm(MFAAuthForm):
    name = forms.CharField(label=_('Name'), max_length=32)
