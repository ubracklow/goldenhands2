from typing import Any

from django.forms import TextInput
from django.forms.renderers import BaseRenderer
from django.utils.html import format_html
from django.utils.safestring import SafeString


class LocationAutocompleteWidget(TextInput):
    class Media:
        js = ('js/location_autocomplete.js',)

    def render(
        self,
        name: str,
        value: str | None,
        attrs: dict[str, Any] | None = None,
        renderer: BaseRenderer | None = None,
    ) -> SafeString:
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
