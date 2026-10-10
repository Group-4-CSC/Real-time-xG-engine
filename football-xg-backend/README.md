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
- `POST /api/xg/calculate/` accepts a shot's distance, angle, and flags, then returns an xG estimate:

	```json
	{
		"distance_to_goal_m": 14,
		"angle_to_goal_deg": 25,
		"is_header": false,
		"is_penalty": false
	}
	```

	The response includes `xg` (between 0 and 1) and the normalized input values. This calculation is a temporary placeholder, not the team's trained xG model; it does not save the shot or integrate Alejandro's analytics module yet.
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
