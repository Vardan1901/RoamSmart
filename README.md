# Roam Smart - Travel Management System

Roam Smart is a comprehensive travel management system that helps users plan, track, and manage their trips efficiently. The application provides features for managing trip details, expenses, and real-time weather information.

## Features

- **Trip Management**
  - Create and manage trips
  - Track trip status (Planning, Active, Completed, Cancelled)
  - Set and monitor trip budgets
  - View trip duration and details

- **Expense Tracking**
  - Record and categorize expenses
  - Upload expense receipts
  - Track budget usage
  - Visualize expenses with charts
  - Get budget alerts

- **Weather Integration**
  - Real-time weather updates
  - 5-day weather forecast
  - Location-based weather information
  - Daily weather summaries

- **User Features**
  - User authentication
  - Personalized trip dashboard
  - Email notifications for budget alerts
  - Responsive design for all devices

## Technology Stack

- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (development)
- **APIs**: OpenWeather API
- **Charts**: Chart.js

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/roam-smart.git
   cd roam-smart
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

4. Set up environment variables:
   - Create a `.env` file
   - Add your OpenWeather API key:
     ```
     OPENWEATHER_API_KEY=your_api_key_here
     ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

1. Register a new account or login
2. Create a new trip with destination and dates
3. Add expenses and upload receipts
4. Monitor your budget and weather updates
5. View expense analytics and trip details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For any queries or support, please open an issue in the GitHub repository. 