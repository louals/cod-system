# COD E-commerce Backend (FastAPI + Supabase)

This is a starter backend for an e-commerce platform focusing on **Cash on Delivery (COD)**.

## Project Structure
- `main.py`: FastAPI entry point with Product and Order endpoints.
- `database.py`: Supabase client initialization.
- `models.py`: Pydantic models for data validation.
- `setup.sql`: SQL commands to create the necessary tables in Supabase.
- `.env`: Environment variables (Supabase URL and Key).

## Getting Started

### 1. Setup Supabase
1. Go to [Supabase](https://supabase.com/) and create a new project.
2. Open the **SQL Editor** in your Supabase dashboard.
3. Copy the content of `setup.sql` and run it to create the tables.
4. Go to **Project Settings > API** and copy your `Project URL` and `anon public` key.

### 2. Configure Environment
1. Update the `.env` file with your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   ```

### 3. Run the Backend
1. Ensure your virtual environment is activated.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
4. Open your browser at `http://127.0.0.1:8000/docs` to see the interactive API documentation.

## COD Workflow
- **Place Order**: Use `POST /orders` with customer details and a list of product IDs/quantities.
- **Stock Management**: The backend automatically reduces stock when an order is placed.
- **Order Tracking**: Use `GET /orders/{id}` to check order status and items.
