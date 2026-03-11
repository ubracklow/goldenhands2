from django.forms import TextInput
from django.utils.html import format_html


class LocationAutocompleteWidget(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        input_id = (attrs or {}).get("id", f"id_{name}")
        list_id = f"{input_id}_suggestions"
        input_html = super().render(name, value, attrs, renderer)

        return format_html(
            """{input}
<ul id="{list_id}" class="location-suggestions" role="listbox" aria-label="Address suggestions"></ul>
<script>
(function() {{
  var input = document.getElementById("{input_id}");
  var list = document.getElementById("{list_id}");
  var timer = null;
  var activeIndex = -1;

  function closeSuggestions() {{
    list.innerHTML = "";
    list.style.display = "none";
    activeIndex = -1;
  }}

  function setActive(items, index) {{
    items.forEach(function(item, i) {{
      item.classList.toggle("active", i === index);
    }});
  }}

  input.addEventListener("input", function() {{
    clearTimeout(timer);
    var q = input.value.trim();
    if (q.length < 3) {{ closeSuggestions(); return; }}
    timer = setTimeout(function() {{
      fetch(
        "https://nominatim.openstreetmap.org/search?format=json&q=" +
        encodeURIComponent(q) + "&limit=5&addressdetails=1",
        {{ headers: {{ "Accept-Language": navigator.language }} }}
      )
      .then(function(r) {{ return r.json(); }})
      .then(function(data) {{
        list.innerHTML = "";
        list.style.display = data.length ? "block" : "none";
        activeIndex = -1;
        data.forEach(function(item) {{
          var li = document.createElement("li");
          li.textContent = item.display_name;
          li.setAttribute("role", "option");
          li.addEventListener("mousedown", function(e) {{
            e.preventDefault();
            input.value = item.display_name;
            closeSuggestions();
          }});
          list.appendChild(li);
        }});
      }})
      .catch(function() {{ closeSuggestions(); }});
    }}, 300);
  }});

  input.addEventListener("keydown", function(e) {{
    var items = Array.from(list.querySelectorAll("li"));
    if (!items.length) return;
    if (e.key === "ArrowDown") {{
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, items.length - 1);
      setActive(items, activeIndex);
    }} else if (e.key === "ArrowUp") {{
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      setActive(items, activeIndex);
    }} else if (e.key === "Enter" && activeIndex >= 0) {{
      e.preventDefault();
      input.value = items[activeIndex].textContent;
      closeSuggestions();
    }} else if (e.key === "Escape") {{
      closeSuggestions();
    }}
  }});

  input.addEventListener("blur", function() {{
    setTimeout(closeSuggestions, 150);
  }});
}})();
</script>""",
            input=input_html,
            list_id=list_id,
            input_id=input_id,
        )
