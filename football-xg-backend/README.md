# Football xG Backend

Django REST Framework starter for the football expected-goals capstone. MongoDB is configured through Django MongoDB Backend. The project intentionally does not define user, match, shot, or CSV schemas yet; those contracts should be agreed on by the team before implementation.

## Requirements

- Python 3.12 or newer
- MongoDB running locally, or a MongoDB connection URI from the team

## Local setup (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Set `MONGODB_URI` and `MONGODB_DATABASE` in `.env` to the values shared by the database owner. The defaults target a local MongoDB server at `mongodb://127.0.0.1:27017` and use the `football_xg` database.

## API

- `GET /api/health/` returns `{"status": "ok"}`. This checks that the API process is responding; it does not check MongoDB connectivity.
- `POST /api/xg/calculate/` accepts a shot in the shared format and returns an xG estimate:

	```json
	{
		"x": 85,
		"y": 50,
		"body_part": "right_foot",
		"outcome": "goal"
	}
	```

	The response is `{"xg": 0.4317, "xg_status": "computed"}` with an xG value between 0 and 1. If the analytics function returns `None` for an unsupported shot, the response is `{"xg": null, "xg_status": "unsupported"}`; the backend does not convert unsupported predictions to zero. Coordinates must be between 0 and 100; `body_part` must be `left_foot`, `right_foot`, `head`, or `other`; and `outcome` must be `goal`, `saved`, `blocked`, `off_target`, or `post`. Invalid requests return HTTP 400. The current `compute_xg(shot)` is a temporary placeholder, ignores the outcome when estimating xG, and does not save the shot. It will be replaced by Alejandro's analytics implementation, which will calculate distance and angle from the shot location.
- Django admin is available at `/admin/` after creating a superuser with `python manage.py createsuperuser`.

Both API endpoints are currently public. Authentication and role-based access are still to be agreed and implemented.

## Tests

```powershell
python manage.py test api
```

## Team contracts to confirm

- MongoDB collections and relationships for users, matches, and shots
- Shot CSV columns and coordinate convention before analytics preprocessing is wired in
- Authentication and role-assignment approach before adding user-facing endpoints
