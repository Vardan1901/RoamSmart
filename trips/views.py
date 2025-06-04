import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from decimal import Decimal
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict
from .models import Trip, Expense
from .forms import TripForm, ExpenseForm
from django.urls import reverse

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"
        if not self.api_key:
            logger.error("OpenWeather API key is not set in settings.py")

    def get_weather(self, lat, lon):
        """Get current weather and 5-day forecast for a location."""
        try:
            if not self.api_key:
                logger.error("Cannot fetch weather: API key is not set")
                return None

            # Get current weather
            current_url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            logger.info(f"Fetching current weather for lat={lat}, lon={lon}")
            current_response = requests.get(current_url, params=params)
            current_response.raise_for_status()
            current_data = current_response.json()

            # Get 5-day forecast
            forecast_url = f"{self.base_url}/forecast"
            logger.info(f"Fetching forecast for lat={lat}, lon={lon}")
            forecast_response = requests.get(forecast_url, params=params)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Process and combine the data
            weather_data = {
                'current': {
                    'temperature': current_data['main']['temp'],
                    'feels_like': current_data['main']['feels_like'],
                    'humidity': current_data['main']['humidity'],
                    'description': current_data['weather'][0]['description'],
                    'icon': current_data['weather'][0]['icon'],
                    'wind_speed': current_data['wind']['speed'],
                    'datetime': datetime.fromtimestamp(current_data['dt']).isoformat(),
                },
                'forecast': []
            }

            # Group forecast data by day
            daily_forecasts = defaultdict(lambda: {
                'temperatures': [],
                'humidity': [],
                'wind_speeds': [],
                'descriptions': defaultdict(int),
                'icons': defaultdict(int)
            })

            # Process forecast data and group by day
            for item in forecast_data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                date_key = dt.strftime('%Y-%m-%d')
                
                daily_forecasts[date_key]['temperatures'].append(item['main']['temp'])
                daily_forecasts[date_key]['humidity'].append(item['main']['humidity'])
                daily_forecasts[date_key]['wind_speeds'].append(item['wind']['speed'])
                daily_forecasts[date_key]['descriptions'][item['weather'][0]['description']] += 1
                daily_forecasts[date_key]['icons'][item['weather'][0]['icon']] += 1

            # Convert grouped data to daily summaries
            for date_key, data in sorted(daily_forecasts.items()):
                dt = datetime.strptime(date_key, '%Y-%m-%d')
                
                # Get most common weather description and icon
                most_common_desc = max(data['descriptions'].items(), key=lambda x: x[1])[0]
                most_common_icon = max(data['icons'].items(), key=lambda x: x[1])[0]
                
                # Calculate averages
                avg_temp = sum(data['temperatures']) / len(data['temperatures'])
                avg_humidity = sum(data['humidity']) / len(data['humidity'])
                avg_wind = sum(data['wind_speeds']) / len(data['wind_speeds'])
                
                # Get min and max temperatures
                min_temp = min(data['temperatures'])
                max_temp = max(data['temperatures'])

                forecast_item = {
                    'date': date_key,
                    'day': dt.strftime('%A'),
                    'temperature': round(avg_temp, 1),
                    'min_temp': round(min_temp, 1),
                    'max_temp': round(max_temp, 1),
                    'description': most_common_desc,
                    'icon': most_common_icon,
                    'humidity': round(avg_humidity),
                    'wind_speed': round(avg_wind, 1),
                }
                weather_data['forecast'].append(forecast_item)

            return weather_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"API Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_weather: {str(e)}")
            return None

    def get_location_coordinates(self, city_name):
        """Get coordinates for a city name."""
        try:
            if not self.api_key:
                logger.error("Cannot fetch location: API key is not set")
                return None

            url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': city_name,
                'limit': 1,
                'appid': self.api_key
            }
            logger.info(f"Fetching coordinates for city: {city_name}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                location = {
                    'lat': data[0]['lat'],
                    'lon': data[0]['lon'],
                    'name': data[0]['name'],
                    'country': data[0]['country']
                }
                logger.info(f"Found coordinates for {city_name}: {location}")
                return location
            
            logger.warning(f"No coordinates found for city: {city_name}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching location data: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"API Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_location_coordinates: {str(e)}")
            return None

# Create your views here.

@login_required
def create_trip(request):
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            
            # Get location coordinates
            weather_service = WeatherService()
            location = weather_service.get_location_coordinates(trip.destination)
            if location:
                trip.latitude = location['lat']
                trip.longitude = location['lon']
            
            trip.save()
            messages.success(request, 'Trip created successfully!')
            return redirect('trip_detail', trip_id=trip.id)
    else:
        form = TripForm()
    return render(request, "trips/trip_form.html", {"form": form, "is_edit": False})


@login_required
def trip_list(request):
    today = timezone.now().date()
    trips = Trip.objects.filter(user=request.user)
    
    # Organize trips based on their dates rather than status
    active_trips = trips.filter(start_date__lte=today, end_date__gte=today)
    upcoming_trips = trips.filter(start_date__gt=today)
    past_trips = trips.filter(end_date__lt=today)
    
    # Get weather data for active trips
    weather_service = WeatherService()
    for trip in active_trips:
        if not trip.weather_data:
            location = weather_service.get_location_coordinates(trip.destination)
            if location:
                trip.latitude = location['lat']
                trip.longitude = location['lon']
                trip.save()
                weather_data = weather_service.get_weather(location['lat'], location['lon'])
                if weather_data:
                    # Store weather data in the database
                    trip.weather_data = weather_data
                    trip.save()
                else:
                    # Clear any existing weather data if fetch failed
                    trip.weather_data = None
                    trip.save()

    return render(request, 'trips/trip_list.html', {
        'active_trips': active_trips,
        'upcoming_trips': upcoming_trips,
        'past_trips': past_trips,
    })


@login_required
def create_expense(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.save()
            
            # Check budget after new expense
            total_expenses = trip.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
            budget_percentage = (total_expenses / trip.budget * 100) if trip.budget else 0
            
            if budget_percentage >= 90:
                messages.warning(request, 'Warning: You have reached 90% of your budget!')
            
            messages.success(request, 'Expense added successfully!')
            return redirect('trip_detail', trip_id=trip.id)
    else:
        form = ExpenseForm()
    return render(request, "trips/expense_form.html", {"form": form, "trip": trip})


@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    expenses = trip.expenses.all().order_by('-date')
    
    # Calculate total expenses and budget remaining
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    budget_remaining = trip.budget - total_expenses
    budget_percentage = (total_expenses / trip.budget * 100) if trip.budget > 0 else 0
    
    # Get weather data
    weather_data = None
    if trip.latitude and trip.longitude:
        weather_service = WeatherService()
        weather_data = weather_service.get_weather(trip.latitude, trip.longitude)
    
    # Prepare expense data for the pie chart
    category_names = {
        'accommodation': 'Accommodation',
        'transportation': 'Transportation',
        'food': 'Food & Dining',
        'activities': 'Activities',
        'shopping': 'Shopping',
        'other': 'Other'
    }
    
    # Group expenses by category and convert Decimal to float
    expenses_by_category = {}
    for expense in expenses:
        category = expense.get_category_display()
        if category not in expenses_by_category:
            expenses_by_category[category] = 0
        expenses_by_category[category] += float(expense.amount)  # Convert Decimal to float
    
    # Convert to list format for the chart
    expense_data = [
        {'category': category, 'amount': float(amount)}  # Ensure amount is float
        for category, amount in expenses_by_category.items()
    ]
    
    # Check budget alerts
    if budget_percentage >= 90 and trip.status == 'active':
        send_mail(
            'Budget Alert',
            f'Your trip to {trip.destination} has reached {budget_percentage:.1f}% of the budget.',
            'noreply@roamsmart.com',
            [request.user.email],
            fail_silently=True,
        )
    
    return render(request, 'trips/trip_detail.html', {
        'trip': trip,
        'expenses': expenses,
        'total_expenses': total_expenses,
        'budget_remaining': budget_remaining,
        'budget_percentage': budget_percentage,
        'weather_data': weather_data,
        'expense_data': expense_data,
    })


@login_required
def edit_expense(request, trip_id, expense_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    expense = get_object_or_404(Expense, id=expense_id, trip=trip)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('trip_detail', trip_id=trip.id)
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'trips/expense_form.html', {
        'form': form,
        'trip': trip,
        'expense': expense,
        'is_edit': True
    })


@login_required
def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        trip.delete()
        messages.success(request, 'Trip deleted successfully.')
        return redirect('trip_list')
    return render(request, 'trips/confirm_delete.html', {
        'object_name': f'Trip to {trip.destination}',
        'cancel_url': reverse('trip_detail', args=[trip.id])
    })


@login_required
def edit_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            # Get new location coordinates if destination changed
            if form.cleaned_data['destination'] != trip.destination:
                weather_service = WeatherService()
                location = weather_service.get_location_coordinates(form.cleaned_data['destination'])
                if location:
                    trip.latitude = location['lat']
                    trip.longitude = location['lon']
                    trip.weather_data = None  # Clear cached weather data
            
            form.save()
            messages.success(request, 'Trip updated successfully.')
            return redirect('trip_detail', trip_id=trip.id)
    else:
        form = TripForm(instance=trip)
    
    return render(request, 'trips/trip_form.html', {
        'form': form,
        'trip': trip,
        'is_edit': True
    })


@login_required
def delete_expense(request, trip_id, expense_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    expense = get_object_or_404(Expense, id=expense_id, trip=trip)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect('trip_detail', trip_id=trip.id)
    return render(request, 'trips/confirm_delete.html', {
        'object_name': f'Expense: {expense.name}',
        'cancel_url': reverse('trip_detail', args=[trip.id])
    })
