# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run inside Docker. Never use a local Python interpreter.

```bash
# Start the app
docker-compose up --build

# Run migrations
docker-compose exec goldenhands python manage.py migrate

# Create new migrations
docker-compose exec goldenhands python manage.py makemigrations

# Run all tests
docker-compose exec goldenhands pytest

# Run a single test class or method
docker-compose exec goldenhands pytest invitations/tests.py::TestAttendeeView
docker-compose exec goldenhands pytest invitations/tests.py::TestAttendeeView::test_post_creates_person_and_attendee
```

## Architecture

Single Django app (`invitations`) with no authentication. The entire flow is stateless — the event PK is passed through URL kwargs at every step.

### Invitation flow (multi-step wizard)

Each step is a separate view. The URL pk changes meaning per step:

| Step | View | URL pk |
|------|------|--------|
| 1 | `StartView` | — |
| 2 | `OrganizerView` / `OrganizerEditView` | organizer (Person) pk |
| 3 | `EventCreateView` / `EventEditView` | organizer pk / event pk |
| 4 | `AttendeeView` | event pk |
| 5 | `TaskView` | event pk |
| 6 | `InviteView` | event pk |
| 7 | `FinalView` | event pk — **sends email on GET** |

Back navigation uses Edit views (`OrganizerEditView`, `EventEditView`) which are `UpdateView`-based counterparts to the create views, sharing config via `OrganizerFormMixin` and `EventFormMixin`.

### Data model

- `Person` — both organizers and attendees; attendees are created fresh on each `AttendeeView` submission and deleted on re-submission.
- `Event` — FK to `Person` (organizer).
- `EventAttendee` — join table between `Event` and `Person` (attendee).
- `EventTask` — FK to `Event` + nullable FK to `EventAttendee` (`SET_NULL`). Tasks survive attendee re-edits with `attendee=null` and get re-assigned when tasks are resubmitted.

Task assignment (`Event.assign_attendee_tasks`) randomly distributes tasks to attendees; if tasks outnumber attendees, some attendees get multiple tasks.

### Forms

- `PersonFormSet` — regular formset (not model formset), `extra=5`. Used for attendees.
- `EventTaskFormSet` — regular formset, `extra=5`. `EventTaskForm.__init__` pops `event` pk from kwargs; `TaskView` passes it via `get_form_kwargs()` as `form_kwargs`.
- `EventForm` — ModelForm for `Event`; date uses `DateTimePickerInput` with `DD/MM/YYYY HH:mm` format; location uses `LocationAutocompleteWidget` (Nominatim/OpenStreetMap autocomplete, inline JS).

### Email

`FinalView.get()` calls `send_email()` immediately on GET — visiting the final URL always sends the email. `EmailMixin` builds the template context shared between the preview (`InviteView`) and the actual send.

### Settings

Config is entirely via environment variables (`.env.dev` locally). `EMAIL_BACKEND` defaults to `console.EmailBackend` if not set. Tests use `pytest-django`; `conftest.py` swaps WhiteNoise static storage for the standard backend to avoid manifest errors.
