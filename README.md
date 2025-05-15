# langgraph_startup_project


# Create and activate virtual environment
python -m venv .venv
source venv/bin/activate  # On Windows: .venv\Scripts\activate

# Navigate to backend directory
cd backend

# Install requirements
pip install -r requirements.txt

# Set up environment variables
# Copy the backend .env template and fill in your values

# Run the backend
python -m uvicorn app.main:app --reload

# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
# Copy the frontend .env template and fill in your values

# Start the development server
npm start


npm install react-hot-toast @types/react @types/react-dom

