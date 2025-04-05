from django import forms
from django.conf import settings


class MultipleFileInput(forms.ClearableFileInput):
  allow_multiple_selected = True


class MultipleFileField(forms.FileField):
  def __init__(self, *args, **kwargs):
    attrs = kwargs.pop('attrs', {})
    attrs['multiple'] = ''
    kwargs.setdefault('widget', MultipleFileInput(attrs=attrs))
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

  def clean_name(self):
    name = self.cleaned_data['name']
    name = name.replace(chr(203), 'Ё').replace(chr(235), 'ё')
    return name



# class BSCharField(forms.CharField):
#   def __init__(self, *args, **kwargs):



class UploadBlanksForm(forms.Form):
  # session = forms.CharField(label='съемка', required=True, widget=forms.TextInput(attrs={'class':'form-control w-auto'}))
  session = forms.ChoiceField(label='съемка', required=True, widget=forms.Select(attrs={'class':'form-control w-auto'}), choices=[(i.name, i.name) for i in (settings.MEDIA_ROOT / 'blanks').iterdir() if i.is_dir()])
  sh = forms.CharField(label='SH', required=True, widget=forms.TextInput(attrs={'class':'form-control w-auto'}))
  # yr = forms.CharField(label='YR', required=True)
  yr = forms.ChoiceField(label="Год", required=True, choices=[
    (i,i) for i in range(1,12)
  ], widget=forms.Select(attrs={'class':'form-select w-auto'}))
  # gr = forms.CharField(label='GR', required=True)
  gr = forms.ChoiceField(label="Класс", required=True, choices=[
    (i, i) for i in 'АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ'
  ], widget=forms.Select(attrs={'class':'form-select w-auto'}))
  #files = forms.FileField(widget=forms.FileInput(attrs={'multiple': True, 'accept':'image/jpeg'}), required=True)
  files = MultipleFileField(required=True, label="Файлы", attrs={'accept': 'image/jpeg', 'style': 'width:0'})

  # class Meta:
  #   widgets = {
  #     "session": forms.TextInput(attrs={"class": "form-control"})
  #   }


