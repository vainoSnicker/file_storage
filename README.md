# File Storage Application

A Django REST Framework application for managing file storage.

## Quick Start

### Step 1: Create Environment File

Create a `.env` file in the root directory with the following content:

```bash
# Database Configuration
POSTGRES_DB=file_storage_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
```

### Step 2: Start Docker Containers

Build and start the application:

```bash
docker compose up -d
```

This will:
- Build the Django application container
- Start PostgreSQL database
- Run database migrations automatically (just in case)
- Start the Django development server on port 8000

### Step 3: Create Test Data

Run the setup script to create test users and organizations:

```bash
./setup_test_data.sh
```

This script creates:
- **Admin user**: `admin` / `adminpass` (Superuser ID: 1)
- **Test User 1**: `testuser1` / `password123` (Organization: Acme Corp)
- **Test User 2**: `testuser2` / `password123` (Organization: Globex Industries)
- **Organizations**: Acme Corp (ID: 1), Globex Industries (ID: 2)

### Step 4: Access the Application

The application is now running! Access it at:

- **API Root**: http://localhost:8000/api/v1/
- **Login Page**: http://localhost:8000/api/v1/auth/login/
- **Admin Panel**: http://localhost:8000/admin/

## Authentication

### Login via Web Interface

1. Navigate to http://localhost:8000/api/v1/auth/login/
2. Enter your credentials:
   - **Username**: `admin` (or `testuser1` / `testuser2`)
   - **Password**: `adminpass` (or `password123`)
3. After successful login, you'll be redirected to the files endpoint

### API Endpoints

Once logged in via the web interface, you can access:

- `GET /api/v1/files/` - List all files
- `POST /api/v1/organizations/<org_id>/files/` - Upload a file to an organization
- `GET /api/v1/files/<file_id>/download/` - Download a file
- `GET /api/v1/organizations/` - List organizations
- `GET /api/v1/users/<user_id>/downloads/` - Get user download history
- `GET /api/v1/files/<file_id>/downloads/` - Get file download history


## Uploading Files

### Via Web Browser (Browsable API)

1. Navigate to http://localhost:8000/api/v1/organizations/1/files/ (replace `1` with your organization ID)
2. Log in if you haven't already
3. Scroll down to the "POST" form section
4. Click "Choose File" and select the file you want to upload
5. Enter a name for the file in the "name" field
6. Click "POST" to upload

### Via API (using curl)

1. First, check your organization ID. If you're using test users:
   - `testuser1` belongs to **Acme Corp** (ID: 1)
   - `testuser2` belongs to **Globex Industries** (ID: 2)

2. Upload a file using curl:

```bash
# For testuser1 (Acme Corp - ID: 1)
curl -X POST \
  http://localhost:8000/api/v1/organizations/1/files/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -F "file=@/path/to/your/file.txt" \
  -F "name=my_file.txt"
```

To get your session ID:
- After logging in via the browser, open Developer Tools (F12)
- Go to Application/Storage → Cookies
- Copy the `sessionid` value

Or use a browser extension to get the cookie from your logged-in session.


## Downloading Files

### Via Web Browser

1. Navigate to http://localhost:8000/api/v1/files/
2. Find the id of the file
3. Go: http://localhost:8000/api/v1/files/{file_id}/download/

The file will be downloaded automatically. Each download creates a record in the download history.


### Reset Database (Start Fresh)

```bash
docker compose down -v
docker compose up -d
./setup_test_data.sh
```

### Running Tests

```bash
docker compose exec web python manage.py test
```
