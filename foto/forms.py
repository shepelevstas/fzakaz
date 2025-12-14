from django import forms
from django.conf import settings

from utils import log

from .models import Session, Album


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
  contact_name = forms.CharField(
      label="ФИО для контакта",
      max_length=60,
      widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Имя для контакта"}),
      required=False,
  )
  name = forms.CharField(
    label="ФИО РЕБЁНКА",
    max_length=60,
    required=False,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "ФИО РЕБЁНКА"}),
  )

  def clean_name(self):
    name = self.cleaned_data['name']
    name = name.replace(chr(203), 'Ё').replace(chr(235), 'ё')
    return name


class UploadBlanksForm(forms.Form):
  session = forms.ChoiceField(label='съемка', required=True, widget=forms.Select(attrs={'class':'form-control w-auto'}), choices=[])
  sh = forms.ChoiceField(label='SH', required=True, widget=forms.Select(attrs={'class': 'form-control w-auto'}), choices=[])
  yr = forms.ChoiceField(label="Год", required=True, choices=[
    (i,i) for i in range(1,12)
  ], widget=forms.Select(attrs={'class':'form-select w-auto'}))
  gr = forms.ChoiceField(label="Класс", required=True, choices=[
    (i, i) for i in 'АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ'
  ], widget=forms.Select(attrs={'class':'form-select w-auto'}))
  files = MultipleFileField(required=True, label="Файлы", attrs={'accept': 'image/jpeg', 'style': 'width:0'})

  def __init__(self, *args, old=False, **kwargs):
    super(UploadBlanksForm, self).__init__(*args, **kwargs)

    if old:
      log(f'[UploadBlanksForm] OLD')
      self.fields['session'].choices = [
        (i.name, i.name)
        for i in (settings.MEDIA_ROOT / 'blanks').iterdir()
        if i.is_dir()
      ]
      self.fields['sh'].choices = [('18', '18'), ('90', '90')]

    else:
      self.fields['session'].choices = [(s.id, str(s)) for s in Session.objects.filter(deleted=None)]
      self.fields['sh'].choices = [(s, s) for s in sorted(set(Album.objects.filter(deleted__isnull=True).values_list('sh', flat=1)))]


