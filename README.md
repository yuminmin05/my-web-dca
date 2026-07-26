# DCA Investment Platform

This Django project provides a simple DCA (Dollar-Cost Averaging) planning experience for Thai stocks and includes a genetic-algorithm based portfolio optimizer.

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the full setup command:
   ```bash
   python manage.py setup_project
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Environment variables

Copy [.env.example](.env.example) to .env and adjust values as needed.

## Main features

- User registration and authentication
- DCA plan configuration
- Stock selection and portfolio optimization via GA
- Investment records and GA history
- PDF export
- Admin panel for stock and plan management
