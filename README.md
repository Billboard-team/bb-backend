# BillBoard Backend

This is a template project for running a Django application using Docker Compose. It simplifies the setup and deployment of your Django app, making it portable and consistent across environments.

---

## Features
- Django backend with a PostgreSQL database
- Environment variable management using `.env` files
- Production-ready setup with Nginx and Gunicorn (optional)
- Separate development and production configurations

---

## Prerequisites

Ensure you have the following installed on your system:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Project Structure
```
project-name/
├── docker/
│   ├── django/
│   │   └── Dockerfile
│   ├── nginx/
│   │   └── nginx.conf
├── django_project/
│   ├── manage.py
│   └── django_project/
├── .env
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the Repository
```bash
git clone <repository-url>
cd project-name
```

### 2. Create an `.env` File

Create a `.env` file in the root directory and configure the following variables:
```dotenv
DJANGO_SECRET_KEY=<your-secret-key>
DEBUG=True
POSTGRES_DB=<database-name>
POSTGRES_USER=<database-user>
POSTGRES_PASSWORD=<database-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### 3. Build and Start the Containers

Run the following command to build and start the Docker containers:
```bash
docker-compose up --build
```

### 4. Run Migrations and Create a Superuser

After starting the containers, run the following commands to set up your database:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the Application

- Django App: [http://localhost:8000](http://localhost:8000)
- Admin Panel: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## Commands Cheat Sheet

### Stop Containers
```bash
docker-compose down
```

### Rebuild Containers
```bash
docker-compose up --build
```

### Run Shell in Django Container
```bash
docker-compose exec web python manage.py shell
```

---

## Troubleshooting

### Common Issues

#### Database Connection Error
- Ensure your `.env` file is correctly configured.
- Restart the containers using:
  ```bash
  docker-compose down && docker-compose up --build
  ```

#### Static Files Not Served in Production
- Ensure your static files are collected using:
  ```bash
  docker-compose exec web python manage.py collectstatic
  ```

---

## Deployment (Optional)

For production deployment, you may:

1. Configure `DEBUG=False` in the `.env` file.
2. Use Gunicorn as the WSGI server.
3. Configure Nginx to serve static files and act as a reverse proxy.

---

## License

This project is licensed under the [MIT License](LICENSE).
