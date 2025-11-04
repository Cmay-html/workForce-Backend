# Node.js CORS Implementation Plan for Workforce Backend

## Overview
Implement secure CORS configuration for the Node.js/Express backend to allow specific frontend origins while maintaining security.

## Current Issue
Frontend deployed on Netlify (https://6908506926707cce75213659--workforceflows.netlify.app) cannot access backend API due to missing CORS headers.

## Implementation Steps

### 1. Install CORS Package
```bash
npm install cors
```

### 2. Create CORS Configuration
Create a dedicated CORS configuration file:

```javascript
// config/cors.js
const corsOptions = {
  origin: function (origin, callback) {
    // Allow requests with no origin (mobile apps, etc.)
    if (!origin) return callback(null, true);

    const allowedOrigins = [
      'https://6908506926707cce75213659--workforceflows.netlify.app',
      'https://workforceflows.netlify.app',
      'http://localhost:3000',    // React dev server
      'http://localhost:5173',    // Vite dev server
      'http://localhost:8080'     // Alternative dev port
    ];

    if (allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  exposedHeaders: ['X-Total-Count', 'X-Page-Count']
};

module.exports = corsOptions;
```

### 3. Update Server Configuration
Modify your main server file (server.js or app.js):

```javascript
// server.js
const express = require('express');
const cors = require('cors');
const corsOptions = require('./config/cors');

const app = express();

// Apply CORS middleware BEFORE other middleware
app.use(cors(corsOptions));

// Your other middleware...
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes...
// app.use('/api', apiRoutes);

module.exports = app;
```

### 4. Environment-Specific Configuration
Create environment-specific CORS settings:

```javascript
// config/cors.js
const getCorsOptions = () => {
  const isProduction = process.env.NODE_ENV === 'production';

  const baseOptions = {
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    exposedHeaders: ['X-Total-Count', 'X-Page-Count']
  };

  if (isProduction) {
    return {
      ...baseOptions,
      origin: [
        'https://6908506926707cce75213659--workforceflows.netlify.app',
        'https://workforceflows.netlify.app'
      ]
    };
  } else {
    return {
      ...baseOptions,
      origin: function (origin, callback) {
        // Allow all localhost origins in development
        if (!origin || origin.includes('localhost')) {
          return callback(null, true);
        }
        callback(new Error('Not allowed by CORS'));
      }
    };
  }
};

module.exports = getCorsOptions();
```

### 5. Error Handling
Add proper CORS error handling:

```javascript
// server.js
app.use((err, req, res, next) => {
  if (err.message === 'Not allowed by CORS') {
    res.status(403).json({
      error: 'CORS Policy Violation',
      message: 'Origin not allowed'
    });
  } else {
    next(err);
  }
});
```

### 6. Testing
Test the CORS configuration:

```javascript
// test/cors.test.js
const request = require('supertest');
const app = require('../server');

describe('CORS Configuration', () => {
  test('should allow requests from allowed origins', async () => {
    const response = await request(app)
      .options('/api/auth/login')
      .set('Origin', 'https://6908506926707cce75213659--workforceflows.netlify.app')
      .set('Access-Control-Request-Method', 'POST');

    expect(response.headers['access-control-allow-origin'])
      .toBe('https://6908506926707cce75213659--workforceflows.netlify.app');
  });

  test('should reject requests from disallowed origins', async () => {
    const response = await request(app)
      .options('/api/auth/login')
      .set('Origin', 'https://malicious-site.com');

    expect(response.status).toBe(403);
  });
});
```

## Deployment Checklist

- [ ] Install `cors` package
- [ ] Create `config/cors.js` with proper configuration
- [ ] Update server.js to use CORS middleware
- [ ] Test CORS with allowed origins
- [ ] Test CORS rejection for disallowed origins
- [ ] Deploy updated backend to Render
- [ ] Verify frontend can access backend API
- [ ] Monitor for any CORS-related errors

## Security Considerations

1. **Specific Origins**: Only allow necessary domains
2. **Credentials**: Enable only if needed for authentication
3. **Headers**: Limit exposed headers to required ones
4. **Methods**: Restrict to necessary HTTP methods
5. **Environment Separation**: Different rules for dev/prod

## Troubleshooting

If CORS issues persist:
1. Check that CORS middleware is applied before routes
2. Verify origin URLs match exactly (including protocol)
3. Check for preflight OPTIONS requests
4. Ensure credentials are handled properly
5. Check browser developer tools for detailed error messages