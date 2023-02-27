from django import forms
from django.utils.translation import gettext_lazy as _


class MFABaseForm(forms.Form):
    code = forms.CharField(label=_('Authentication code'))

    def __init__(self, validate_code=None, **kwargs):
        self.validate_code = validate_code
        super().__init__(**kwargs)

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        if code:
            try:
                cleaned_data['secret'] = self.validate_code(code)
            except ValueError as e:
                raise forms.ValidationError(_('Validation failed')) from e
        return cleaned_data


class MFAAuthForm(MFABaseForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['code'].widget.attrs.update({'autofocus': True})


class MFACreateForm(MFABaseForm):
    name = forms.CharField(label=_('Name'), max_length=32)
