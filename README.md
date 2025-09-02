# 🎬 Online Cinema API

A scalable and modular backend API for an online movie streaming and purchasing platform. Built with FastAPI,
PostgreSQL, Celery, and Docker, this backend supports user management, movie catalog operations, shopping cart flows,
Stripe payments, and secure asset handling.

## 🚀 How to Run the Project

### 1. 📥 Clone the Repository

 ```git clone bash 
https://github.com/boris-devs/online_cinema_api.git
```

### 2. ⚙️ Create and Configure Environment Variables
Create a .env file based on the provided .env.sample
Then, open the .env file and replace the placeholder values with your actual configuration (e.g., database credentials, secret keys, Stripe keys, etc.).

Make sure the src directory is marked as Sources Root in your IDE (e.g., in PyCharm or VS Code) for correct module resolution.

### 3. 📦 Install Dependencies with Poetry
Ensure Poetry is installed on your system.

Install the project dependencies:
```bash
poetry install
```
### 5. 🐳 Start the Application with Docker
Use Docker Compose to build and start the development environment:

```bash
docker compose -f docker-compose-dev.yml up --build
```
This command will build all necessary images and start the containers as defined in docker-compose-dev.yml.

### 6. 💳 Test Stripe Webhooks Locally

This command simulates the checkout.session.completed event, allowing you to use webhook handling logic.
```bash
stripe trigger checkout.session.completed
```
For more triggers check stripe-cli docs
## 📌 Key Features

- **JWT Authentication** with refresh and access tokens
- **Email-based account activation** with expiration logic
- **Password reset** using time-limited tokens
- **Role-based access control (RBAC)** for User, Moderator, Admin
- **Full movie catalog**: genre, director, actor, certification, filtering, sorting
- **Favorites, comments, ratings, likes/dislikes**
- **Shopping cart and order processing**
- **Stripe integration** for payment lifecycle management
- **S3-compatible MinIO object storage** for user media
- **Celery with beat** for background tasks (e.g., token cleanup)
- **Dockerized stack with service health checks and environment parity**

---

## 🧠 Techniques Used

- **[JWT](https://developer.mozilla.org/en-US/docs/Web/API/Web_Tokens)** for secure user sessions
- **[Celery](https://docs.celeryq.dev/en/stable/)** + Beat for async and scheduled tasks
- **[Docker Health Checks](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)** to delay
  dependent service startup
- **[Stripe Webhooks](https://stripe.com/docs/webhooks)** for real-time transaction updates
- **Database token expiry logic** tied to periodic cleanup jobs
- **Immutable pricing** snapshots in order/payment records
- **RBAC enforcement** through enum-bound foreign keys
- **MinIO S3** asset storage using presigned URLs

---

## 🛠 Notable Technologies & Libraries

- [FastAPI](https://fastapi.tiangolo.com/) – web framework
- [SQLAlchemy](https://docs.sqlalchemy.org/) – ORM
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) – migrations
- [MinIO](https://min.io/) – object storage
- [Mailhog](https://github.com/mailhog/MailHog) – local email catcher
- [pgAdmin](https://www.pgadmin.org/) – PostgreSQL admin GUI
- [Stripe Python SDK](https://github.com/stripe/stripe-python) – payments
- [Passlib](https://passlib.readthedocs.io/) – secure password hashing
- [Uvicorn](https://www.uvicorn.org/) – ASGI server  

