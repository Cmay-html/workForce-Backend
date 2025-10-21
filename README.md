# Workforce Backend

A Node.js/Express backend API for a workforce management platform with user authentication, profiles, and messaging.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **User Management**: CRUD operations for users with role-based access control
- **Profiles**: Comprehensive user profiles with experience, education, and skills
- **Messaging**: Internal messaging system with moderation capabilities
- **Security**: Helmet, CORS, rate limiting, and input validation
- **Logging**: Winston-based logging with file and console outputs
- **Database**: MongoDB with Mongoose ODM

## Tech Stack

- **Runtime**: Node.js
- **Framework**: Express.js
- **Database**: MongoDB with Mongoose
- **Authentication**: JWT (JSON Web Tokens)
- **Security**: Helmet, CORS, bcrypt, express-rate-limit
- **Logging**: Winston
- **Validation**: Built-in Mongoose validation

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- MongoDB (local or cloud instance)
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd workforce-backend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Configure your environment variables in `.env`:
   ```
   MONGODB_URI=mongodb://localhost:27017/workforce
   JWT_SECRET=your_super_secret_jwt_key_here
   PORT=5000
   NODE_ENV=development
   LOG_LEVEL=debug
   ```

5. Start MongoDB service (if running locally)

6. Start the server:
   ```bash
   npm start
   ```

The server will start on port 5000 (or the port specified in your `.env` file).

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh JWT token

### Users
- `GET /api/users` - Get all users (admin only)
- `GET /api/users/:id` - Get user by ID
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user (admin only)
- `PUT /api/users/:id/password` - Change password

### Profiles
- `GET /api/profiles/me` - Get current user's profile
- `GET /api/profiles/:userId` - Get profile by user ID
- `POST /api/profiles` - Create profile
- `PUT /api/profiles/me` - Update profile
- `DELETE /api/profiles/me` - Delete profile
- `GET /api/profiles` - Get public profiles with search

### Messages
- `GET /api/messages` - Get user's messages
- `GET /api/messages/:id` - Get message by ID
- `POST /api/messages` - Send message
- `PUT /api/messages/:id` - Update message (mark as read/unread)
- `DELETE /api/messages/:id` - Delete message
- `PUT /api/messages/:id/moderate` - Moderate message (moderator/admin)
- `GET /api/messages/moderation/pending` - Get messages pending moderation

### Health Check
- `GET /health` - Server health check

## User Roles

- **user**: Basic user with access to their own data
- **moderator**: Can moderate messages and access moderation tools
- **admin**: Full access including user management

## Development

### Scripts

- `npm start` - Start the server
- `npm run dev` - Start with nodemon (if installed)
- `npm test` - Run tests (when implemented)

### Project Structure

```
workforce-backend/
├── models/           # Mongoose models
│   ├── User.js
│   ├── Profile.js
│   └── Message.js
├── routes/           # API routes
│   ├── auth.js
│   ├── users.js
│   ├── profiles.js
│   └── messages.js
├── middleware/       # Custom middleware
│   └── auth.js
├── utils/            # Utility functions
│   └── logger.js
├── logs/             # Log files
├── server.js         # Main server file
├── .env              # Environment variables
├── package.json
└── README.md
```

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Rate limiting
- Helmet security headers
- CORS configuration
- Input validation and sanitization
- Role-based access control

## Logging

Logs are stored in the `logs/` directory:
- `error.log` - Error-level logs
- `all.log` - All log levels

Log levels: error, warn, info, http, debug

## Deployment

### Environment Variables for Production

```
NODE_ENV=production
MONGODB_URI=mongodb://username:password@host:port/database
JWT_SECRET=your_production_jwt_secret
PORT=5000
LOG_LEVEL=info
```

### Docker (Optional)

```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 5000
CMD ["npm", "start"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the ISC License.