from django import forms

from foto.forms import MultipleFileField, MultipleFileInput


class UploadAlbumForm(forms.Form):
  album = forms.CharField(label='альбом', required=True)
  #files = forms.FileField(widget=forms.FileInput(attrs={'multiple': True, 'accept':'image/jpeg'}), required=True)
  files = MultipleFileField(required=True, widget=MultipleFileInput(attrs={
    'multiple': '',
    'accept': 'image/jpeg',
  }))



