from django import forms
from .models import Playlist


class PlaylistInputForm(forms.ModelForm):
    playlist_id = forms.CharField(
        label="Spotify Playlist URI",
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "Paste the URI here"}),
    )

    class Meta:
        model = Playlist
        fields = ["playlist_id"]

    def clean_id(self):
        data = self.cleaned_data["playlist_id", "playlist_num_tracks", "playlist_url", "playlist_name"]
        return data
