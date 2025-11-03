# Workforce Backend

A Flask-RESTful backend API for a workforce management platform connecting clients and freelancers. Built with modern Python technologies and PostgreSQL database.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Role-Based Access Control**: Multi-user roles (Admin, Client, Freelancer) with specific permissions
- **Project Management**: Complete project lifecycle from posting to completion
- **Payment Processing**: Integrated payment system with invoice generation
- **Messaging System**: Internal messaging between users with moderation
- **File Management**: Cloudinary integration for image uploads and optimization
- **Email Integration**: SendGrid for notifications and verification emails
- **Admin Dashboard**: Analytics and dispute resolution capabilities
- **Security**: CORS, input validation, and secure credential handling
- **API Documentation**: Swagger/OpenAPI documentation for all endpoints

## Tech Stack

- **Runtime**: Python 3.8+
- **Framework**: Flask-RESTful (Flask-RESTX)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (Flask-JWT-Extended)
- **Serialization**: Marshmallow
- **Security**: Flask-CORS, bcrypt, input sanitization
- **Email**: SendGrid
- **File Storage**: Cloudinary
- **Migration**: Flask-Migrate (Alembic)
- **Testing**: pytest

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

### Installation

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd workforce-backend
    ```

2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    Create a `.env` file in the root directory with the following variables:
    ```env
    SECRET_KEY=your-secret-key-here
    JWT_SECRET_KEY=your-jwt-secret-key-here
    DATABASE_URI=postgresql+psycopg2://username:password@localhost:5432/workforce_db
    SENDGRID_API_KEY=your-sendgrid-api-key
    CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
    FLASK_ENV=development
    ```

5. Set up the database:
    ```bash
    # Create PostgreSQL database
    createdb workforce_db

    # Run migrations
    flask db upgrade
    ```

6. Seed the database (optional):
    ```bash
    python seed.py
    ```

7. Start the development server:
    ```bash
    python run.py
    ```

The API will be available at `http://localhost:5000` with Swagger documentation at `http://localhost:5000/swaggerui`.

## API Endpoints

### Authentication (`/api/auth`)
- `POST /auth/login` - User login with JWT token generation
- `POST /auth/signup` - User registration (not implemented in routes)

### Admin Operations (`/api/admin`)
- `GET /admin/users` - List all users with pagination
- `POST /admin/users` - Create new user
- `GET /admin/users/<id>` - Get user by ID
- `DELETE /admin/users/<id>` - Delete user
- `GET /admin/disputes` - List all disputes
- `PUT /admin/disputes/<id>/resolve` - Resolve dispute
- `GET /admin/analytics` - Get system analytics

### Applications (`/api/applications`)
- `GET /applications` - List project applications (freelancer)
- `POST /applications` - Create new application
- `GET /applications/<id>` - Get application details
- `PUT /applications/<id>` - Update application
- `DELETE /applications/<id>` - Delete application

### Projects (`/api/projects`)
- `GET /projects` - List projects based on user role
- `POST /projects` - Create new project (client only)
- `GET /projects/<id>` - Get project details
- `PUT /projects/<id>` - Update project
- `GET /projects/<id>/applications` - Get project applications
- `POST /projects/<id>/hire` - Hire freelancer for project

### Payments (`/api/client/payments`, `/api/freelancer/payments`)
- `GET /client/payments` - List client payments
- `POST /client/payments/initiate` - Initiate payment
- `GET /client/payments/verify/<tx_ref>` - Verify payment
- `GET /freelancer/payments` - List freelancer receipts

### Invoices (`/api/invoices`)
- `GET /invoices` - List invoices
- `POST /invoices` - Create invoice
- `GET /invoices/<id>` - Get invoice details
- `PUT /invoices/<id>` - Update invoice
- `DELETE /invoices/<id>` - Delete invoice
- `GET /invoices/calculate/<job_id>` - Calculate invoice amount

### Reviews (`/api/reviews`)
- `GET /reviews` - List reviews based on user role
- `POST /reviews` - Create review
- `GET /reviews/<id>` - Get review details
- `PUT /reviews/<id>` - Update review
- `DELETE /reviews/<id>` - Delete review
- `GET /reviews/freelancer/<id>` - Get freelancer reviews

### Freelancer Operations (`/api/freelancer`)
- `GET /freelancer/profile` - Get freelancer profile
- `PUT /freelancer/profile` - Update freelancer profile
- `GET /freelancer/projects` - List freelancer projects
- `GET /freelancer/applications` - List freelancer applications
- `POST /freelancer/projects/<id>/apply` - Apply to project

### Milestones (`/api/milestones`)
- `GET /milestones` - List milestones
- `POST /milestones` - Create milestone
- `GET /milestones/<id>` - Get milestone details
- `PUT /milestones/<id>` - Update milestone
- `DELETE /milestones/<id>` - Delete milestone
- `PUT /milestones/<id>/approve` - Approve milestone
- `PUT /milestones/<id>/reject` - Reject milestone
- `GET /milestones/project/<id>` - Get project milestones

### Time Entries (`/api/time-entries`)
- `GET /time-entries` - List time entries
- `POST /time-entries` - Create time entry
- `GET /time-entries/<id>` - Get time entry details
- `PUT /time-entries/<id>` - Update time entry
- `DELETE /time-entries/<id>` - Delete time entry

### Deliverables (`/api/deliverables`)
- `GET /deliverables` - List deliverables
- `POST /deliverables` - Create deliverable
- `GET /deliverables/<id>` - Get deliverable details
- `PUT /deliverables/<id>` - Update deliverable
- `DELETE /deliverables/<id>` - Delete deliverable
- `POST /deliverables/upload` - Upload deliverable file

## User Roles

- **admin**: Full system access including user management, dispute resolution, and analytics
- **client**: Can post projects, hire freelancers, manage payments, and leave reviews
- **freelancer**: Can apply to projects, submit deliverables, track time, and manage profile

## Development

### Scripts

- `python run.py` - Start the Flask development server
- `python -m pytest` - Run test suite
- `flask db upgrade` - Run database migrations
- `python seed.py` - Seed database with sample data

### Project Structure

```
workforce-backend/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── auth.py             # Authentication utilities
├── extensions.py       # Flask extensions initialization
├── utils.py            # Utility functions
├── models/             # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── project.py
│   ├── payment.py
│   ├── invoice.py
│   ├── milestone.py
│   ├── deliverable.py
│   ├── review.py
│   ├── message.py
│   ├── time_log.py
│   ├── skill.py
│   ├── dispute.py
│   └── policy.py
├── routes/             # API route handlers
│   ├── __init__.py
│   ├── routes.py       # Admin and auth routes
│   ├── auth.py
│   ├── applications.py
│   ├── projects.py
│   ├── payments.py
│   ├── payment.py
│   ├── invoices.py
│   ├── reviews.py
│   ├── freelancer.py
│   ├── milestone.py
│   ├── time-entries.py
│   ├── deliverables.py
│   └── receipts.py
├── migrations/         # Database migrations
├── test_*.py           # Test files
├── requirements.txt    # Python dependencies
├── Pipfile             # Alternative dependency management
├── pytest.ini          # Test configuration
├── seed.py             # Database seeding script
├── run.py              # Development server runner
├── .env                # Environment variables
├── .gitignore
└── README.md
```

## Security Features

- JWT token authentication with configurable expiration
- Password hashing using Werkzeug security
- Role-based access control with decorators
- CORS configuration for cross-origin requests
- Input validation through Flask-RESTX models
- SQL injection prevention via SQLAlchemy ORM
- Secure handling of sensitive environment variables

## Database Design

The application uses PostgreSQL with the following key relationships:

- **Users** have one-to-one relationships with **ClientProfiles** or **FreelancerProfiles**
- **Projects** belong to **Clients** and can be assigned to **Freelancers**
- **Projects** have multiple **Milestones** and **Applications**
- **Payments** are linked to **Invoices** and **Projects**
- **Reviews** connect **Clients** with **Freelancers**
- **TimeLogs** track work on **Projects**
- **Deliverables** are submitted for **Milestones**

All models follow 2NF normalization principles with proper foreign key relationships.

## Deployment

### Environment Variables for Production

```env
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-secret
DATABASE_URI=postgresql+psycopg2://user:password@host:port/database
SENDGRID_API_KEY=your-sendgrid-api-key
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
FLASK_ENV=production
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

### Render/Heroku Deployment

1. Set environment variables in hosting platform
2. Use PostgreSQL add-on for database
3. Configure build command: `pip install -r requirements.txt`
4. Configure start command: `gunicorn run:app`

## Testing

Run the test suite using pytest:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test file
python -m pytest test_models.py
```

## API Documentation

The API is fully documented using Swagger/OpenAPI. When running the development server, visit:
- Swagger UI: `http://localhost:5000/swaggerui`
- OpenAPI JSON: `http://localhost:5000/swagger.json`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Code Quality

This project follows these coding standards:
- **Linting**: Use Flake8 for Python code quality
- **Formatting**: Follow PEP 8 style guidelines
- **Testing**: Maintain test coverage above 80%
- **Documentation**: Document all public APIs and complex logic

## License

This project is licensed under the MIT License - see the LICENSE file for details.