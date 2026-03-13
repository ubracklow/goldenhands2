from django.forms import TextInput
from django.utils.html import format_html


class LocationAutocompleteWidget(TextInput):
    class Media:
        js = ('js/location_autocomplete.js',)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        input_id = attrs.get('id', f'id_{name}')
        list_id = f'{input_id}_suggestions'
        attrs['data-list-id'] = list_id
        input_html = super().render(name, value, attrs, renderer)
        return format_html(
            '{}<ul id="{}" class="location-suggestions" role="listbox" aria-label="Address suggestions"></ul>',
            input_html,
            list_id,
        )
