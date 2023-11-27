from django import forms


class MultipleFileInput(forms.ClearableFileInput):
  allow_multiple_selected = True


class MultipleFileField(forms.FileField):
  def __init__(self, *args, **kwargs):
    kwargs.setdefault('widget', MultipleFileInput())
    super().__init__(*args, **kwargs)

  def clean(self, data, initial=None):
    single_file_clean = super().clean
    if isinstance(data, (list, tuple)):
      result = [single_file_clean(d, initial) for d in data]
    else:
      result = single_file_clean(data, initial)
    return result


class ContactInfoForm(forms.Form):
  tel = forms.CharField(
    label="Телефон",
    max_length=11,
    required=True,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}),
  )
  mail = forms.EmailField(
    label='Почта',
    max_length=150,
    required=True,
    widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Почта'}),
  )
  name = forms.CharField(
    label="ФИО РЕБЁНКА",
    max_length=60,
    required=True,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "ФИО РЕБЁНКА"}),
  )


class UploadBlanksForm(forms.Form):
  sh = forms.CharField(label='SH', required=True)
  yr = forms.CharField(label='YR', required=True)
  gr = forms.CharField(label='GR', required=True)
  #files = forms.FileField(widget=forms.FileInput(attrs={'multiple': True, 'accept':'image/jpeg'}), required=True)
  files = MultipleFileField(required=True)


