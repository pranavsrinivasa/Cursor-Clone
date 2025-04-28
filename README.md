# Agentic AI Code Assistant

This project is an agentic AI system that helps with codebase understanding and modification. It can ingest a repository, analyze its structure, and make changes based on user requirements.

## Features

- Codebase ingestion and analysis
- Implementation planning based on user requirements
- Automated code changes with testing
- Git integration for version control
- API endpoints for interacting with the system

## Project Structure

```
- Backend/
  - agents.py        # Core agent components
  - app.py           # Flask API endpoints
  - masteragent.py   # Main orchestration logic
  - classes.py       # Data models
  - utils.py         # Utility functions
```

## Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- Git
- Google Gemini API key

## Backend Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the Backend directory with your Google API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

5. Run the Flask server:
   ```bash
   cd Backend
   python app.py
   ```

   The server will run on `http://localhost:5000` by default.

## Frontend Setup

1. Create a new React app:
   ```bash
   npx create-react-app frontend
   cd frontend
   ```

2. Install required dependencies:
   ```bash
   npm install
   ```

3. Create API service:
   Create a file `src/services/api.js` with the following content:

   ```javascript
   import axios from 'axios';

   const API_URL = 'http://localhost:5000';

   export const submitRequirement = async (repoPath, prompt) => {
     try {
       const response = await axios.post(`${API_URL}/chatv1`, {
         repo_path: repoPath,
         prompt: prompt
       });
       return response.data;
     } catch (error) {
       console.error('Error submitting requirement:', error);
       throw error;
     }
   };

   export const getPendingChanges = async () => {
     try {
       const response = await axios.get(`${API_URL}/pending_changes`);
       return response.data.pending_changes;
     } catch (error) {
       console.error('Error getting pending changes:', error);
       throw error;
     }
   };

   export const getFileChanges = async (changeId) => {
     try {
       const response = await axios.post(`${API_URL}/get_file_changes`, {
         change_id: changeId
       });
       return response.data;
     } catch (error) {
       console.error('Error getting file changes:', error);
       throw error;
     }
   };

   export const acceptChanges = async (changeId) => {
     try {
       const response = await axios.post(`${API_URL}/accept_changes`, {
         change_id: changeId
       });
       return response.data;
     } catch (error) {
       console.error('Error accepting changes:', error);
       throw error;
     }
   };
   ```

4. Start the React development server:
   ```bash
   npm start
   ```

   The frontend will run on `http://localhost:3000`.

## API Endpoints

- `POST /chatv1`: Submit a code modification requirement
  ```json
  {
    "repo_path": "/path/to/repo",
    "prompt": "Your requirement here"
  }
  ```

- `GET /pending_changes`: List all pending code changes

- `POST /get_file_changes`: Get details of file changes for a specific change ID
  ```json
  {
    "change_id": "change-id-here"
  }
  ```

- `POST /accept_changes`: Accept and commit changes to the repository
  ```json
  {
    "change_id": "change-id-here",
    "commit_message": "Optional custom commit message"
  }
  ```

## Usage Flow

1. Submit a requirement through the API or UI
2. Review the proposed changes
3. Accept or reject the changes
4. If accepted, changes are committed to the repository

## Notes

- Ensure the Flask backend is running before using the frontend
- The system creates backups of original files before making changes
- You can modify the repository paths in the code to match your environment
- For large codebases, the initial indexing process may take some time

## Troubleshooting

- If you encounter CORS errors, ensure the Flask CORS configuration is correctly set up
- Check that your Gemini API key is valid and has sufficient permissions
- Make sure the repository paths are accessible by the application
