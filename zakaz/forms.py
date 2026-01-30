from django import forms
from django.conf import settings

from utils import log

from .models import Session, Album, School, Pricelist


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


class UploadBlanksForm(forms.Form):
  session = forms.ChoiceField(label="съемка", required=True, widget=forms.Select(attrs={'class': 'form-control w-auto'}), choices=[])
  sh = forms.ChoiceField(label="SH", required=True, widget=forms.Select(attrs={'class': 'form-control w-auto'}), choices=[])
  yr = forms.ChoiceField(label="Год", required=True, choices=[
    (i, i) for i in range(1, 12)
  ], widget=forms.Select(attrs={'class': 'form-select w-auto'}))
  gr = forms.ChoiceField(label="Класс", required=True, choices=[
    (i, i) for i in 'АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ'
  ], widget=forms.Select(attrs={'class': 'form-select w-auto'}))
  files = MultipleFileField(required=True, label="Файлы", attrs={'accept': 'image/jpeg', 'style': 'width:0'})

  def __init__(self, *args, **kwargs):
    super(UploadBlanksForm, self).__init__(*args, **kwargs)

    self.fields['session'].choices = [(s.id, str(s)) for s in Session.objects.filter(deleted=None)]
    self.fields['sh'].choices = [(s.id, s.name) for s in School.objects.filter(deleted=None).order_by('name')]
