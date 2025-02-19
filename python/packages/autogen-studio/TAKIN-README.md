# AutoGen Studio Setup Guide

## Local Environment Setup

### Prerequisites
- Python 3.10+
- Node.js 14.15.0+
- PostgreSQL

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/datamonet/autogen-beta.git
cd autogen-beta/python/packages/autogen-studio
```

2. Create a PostgreSQL database: `autogen`

3. Configure Environment Variables:
The `.autogenstudio-workspace` directory is used to store AutoGen-related data and configuration files. You'll need to set up the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `TAKIN_API_URL`: URL for Takin user data API (default: http://localhost:3000)
- `AUTOGENSTUDIO_DATABASE_URI`: use `postgresql://postgres:@localhost:5432/autogen` for local testing
- `DEPLOY_ENV`: use `PRODUCTION` for production, `TESTING` for local testing (default: PRODUCTION)

Create your environment file by copying the example:
```bash
cp .autogenstudio-workspace/.env.example .autogenstudio-workspace/.env
```

Then edit `.autogenstudio-workspace/.env` with your specific configuration values.

4. Install Python Dependencies:
```bash
pip install -e .
```

5. Set Up the Frontend:
Navigate to the frontend directory and install the required dependencies:
```bash
# Install global dependencies
npm install -g gatsby-cli
npm install --global yarn
```

```
# Install and build frontend
cd frontend
yarn install
```

Then build the frontend:

- For production, do this: `yarn build`, which will use `frontend/.env.production` and set `GATSBY_TAKIN_API_URL=https://takin.ai`
- For local development, do this: `yarn build-dev`, which will use `frontend/.env.development` and set `GATSBY_TAKIN_API_URL=http://localhost:3000`

6. Start the Application:
```bash
cd ..
autogenstudio ui
```

The application will be available at http://localhost:3002 by default.

## Development Notes

### Frontend Development

- After making any changes to the frontend code, you must rebuild using `yarn build` or `yarn build-dev` for the changes to take effect
- The built frontend files are automatically copied to `../autogenstudio/web/ui/` during the build process

### File Structure
- `.autogenstudio-workspace/`: Contains application data and configuration
  - `.env`: Main configuration file (not version controlled)
  - `.env.example`: Template for configuration (version controlled)
- `frontend/`: Contains all frontend-related code
- `autogenstudio/`: Contains the backend Python code
