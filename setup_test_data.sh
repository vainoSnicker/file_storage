#!/bin/bash
# Script to create initial organizations and users for the file storage application

# Check if the web container is running
if ! docker compose ps -q web | grep -q .; then
    echo "Error: The 'web' service is not running. Please run 'docker compose up -d' first."
    exit 1
fi

echo "--- 1. Running Migrations ---"
docker compose exec web python manage.py migrate --no-input

echo "--- 2. Creating Superuser (Admin) ---"
# Create an admin user
docker compose exec -T web python manage.py shell <<'PYEOF'
from files.models import User
from django.contrib.auth.hashers import make_password
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True,
        'password': make_password('adminpass'),
    }
)
if created:
    print(f"Created Superuser: {admin_user.username}")
else:
    print(f"Superuser already exists: {admin_user.username}")
PYEOF

echo "--- 3. Creating Organizations and Regular Users ---"

# Command to create organizations and users
docker compose exec -T web python manage.py shell <<'PYEOF'
from files.models import User, Organization
from django.contrib.auth.hashers import make_password

# --- Organization 1 & User 1 ---
org1, created = Organization.objects.get_or_create(name='Acme Corp')
print(f"Organization 1: {org1.name} (ID: {org1.id})")

user1, created = User.objects.get_or_create(
    username='testuser1', 
    defaults={
        'email': 'user1@acme.com', 
        'password': make_password('password123'),
        'organization': org1
    }
)
if created:
    print(f"Created user: {user1.username} in {org1.name} (Password: password123)")
else:
    print(f"User already exists: {user1.username}")

# --- Organization 2 & User 2 ---
org2, created = Organization.objects.get_or_create(name='Globex Industries')
print(f"Organization 2: {org2.name} (ID: {org2.id})")

user2, created = User.objects.get_or_create(
    username='testuser2', 
    defaults={
        'email': 'user2@globex.com', 
        'password': make_password('password123'),
        'organization': org2
    }
)
if created:
    print(f"Created user: {user2.username} in {org2.name} (Password: password123)")
else:
    print(f"User already exists: {user2.username}")
PYEOF

echo "--- Test Data Setup Complete! ---"
echo "Organizations: Acme Corp (ID 1), Globex Industries (ID 2)"
echo "Users: admin/adminpass (Superuser), testuser1/password123, testuser2/password123"