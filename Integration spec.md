# PrepPal ML API - Complete Integration Specification
**Version:** 3.1  
**Last Updated:** February 23, 2026  
**API Owner:** Euodia Sam (Data Science Lead)

## Critical Information

**API Base URL:** `http://192.168.1.181:8502` (ngrok public url)

> This URL is served via ngrok tunnelling to local port `8000`. If ngrok restarts, the URL changes. Update it in your backend service class, mobile app, and DevOps scripts when it does.

**This document defines EXACT contracts between ML API and other systems. Following these specs prevents crashes.**
> NOTE: It is meant to give a fair idea on how to integrate the model, not a replacement to your actual code
---

## Table of Contents

1. [API Endpoints Contract](#api-endpoints-contract)
2. [Data Models (JSON Schemas)](#data-models-json-schemas)
3. [Backend Requirements](#backend-requirements)
4. [Mobile App Requirements](#mobile-app-requirements)
5. [DevOps Requirements](#devops-requirements)
6. [Error Handling](#error-handling)
7. [Testing Checklist](#testing-checklist)

---

## API Endpoints Contract

### 1. Health Check

**Endpoint:** `GET /api/health`

**Purpose:** DevOps uses this for uptime monitoring. Backend should check this before calling other endpoints.

**Request:** None

**Response (200 OK - Healthy):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_error": null,
  "timestamp": "2026-02-23T10:30:00",
  "version": "3.0.0"
}
```

**Response (200 OK - Degraded):**
```json
{
  "status": "degraded",
  "model_loaded": false,
  "model_error": "Error loading model file",
  "timestamp": "2026-02-23T10:30:00",
  "version": "3.0.0"
}
```

**Backend Action:** If status != "healthy", use cached predictions or show maintenance message.

**DevOps Action:** Alert if status != "healthy" for > 5 minutes. Both responses return HTTP 200 -- check the status field, not the HTTP code.

---

### 2. Single-Day Prediction

**Endpoint:** `POST /api/predict`

**Purpose:** Get tomorrow's demand forecast for one menu item.

**Request Body:**
```json
{
  "item_name": "Jollof Rice",
  "business_type": "Restaurant",
  "date": "2025-12-01",
  "price": 50,
  "shelf_life_hours": 4,
  "weather": "Clear",
  "is_holiday": 0
}
```

**Field Requirements:**

| Field | Type | Required | Valid Values | Notes |
|-------|------|----------|--------------|-------|
| item_name | string | YES | Any text | Case-sensitive. "jollof rice" != "Jollof Rice" |
| business_type | string | YES | "Restaurant", "Cafe", "Bakery" | EXACT spelling, capital first letter |
| date | string | YES | "YYYY-MM-DD" | ISO 8601 format only |
| price | float | YES | > 0 | Must be positive number |
| shelf_life_hours | float | YES | > 0 | 0.5 for coffee, 4 for jollof, 24 for bread |
| weather | string | NO (default: "Clear") | "Clear", "Rainy" | Only these 2 values accepted |
| is_holiday | int | NO (default: 0) | 0 or 1 | 0 = regular day, 1 = holiday |

**Success Response (200 OK):**
```json
{
  "success": true,
  "fallback": false,
  "date": "2025-12-01",
  "predicted_demand": 42,
  "recommended_quantity": 44,
  "confidence": "High",
  "confidence_score": 0.85,
  "explanation": "Based on: weekday pattern, rolling average, weather",
  "is_new_item": false
}
```

**Fallback Response (200 OK - Cached forecast available):**
```json
{
  "success": true,
  "fallback": true,
  "fallback_reason": "Model temporarily unavailable - showing last valid forecast",
  "predicted_demand": 42,
  "recommended_quantity": 44,
  "confidence": "High",
  "confidence_score": 0.85
}
```

**Fallback Response (200 OK - No cache available):**
```json
{
  "success": true,
  "fallback": true,
  "fallback_reason": "Model unavailable. Please use recent sales history as a guide.",
  "predicted_demand": null
}
```

**Note:** `recommended_quantity` is not returned when there is no cached forecast. Always check for its presence before accessing it.

**Error Response (400 Bad Request):**
```json
{
  "detail": {
    "success": false,
    "error": "price must be greater than 0"
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "detail": {
    "success": false,
    "error": "Model prediction failed",
    "traceback": "..."
  }
}
```

**Backend Requirements:**
1. Validate input before sending (check business_type spelling)
2. Handle both success and fallback responses (both have success: true)
3. Do not assume recommended_quantity exists in fallback -- check for it first
4. Store predictions in database with timestamp
5. If API returns 500, use yesterday's forecast as backup
6. Never show error to user, always have a fallback

**Mobile Requirements:**
1. Show loading indicator while waiting (response time: <2 seconds)
2. Display confidence with color: High=green, Medium=yellow, Low=orange
3. If fallback=true, show warning icon: "Using cached forecast"
4. Handle network timeout (set timeout to 10 seconds)

---

### 3. 7-Day Forecast

**Endpoint:** `POST /api/predict-week`

**Purpose:** Get week-ahead predictions for planning.

**Request Body:**
```json
{
  "item_name": "Jollof Rice",
  "business_type": "Restaurant",
  "price": 50,
  "shelf_life_hours": 4,
  "starting_date": "2025-12-01",
  "weather_forecast": ["Clear","Clear","Rainy","Clear","Clear","Clear","Rainy"],
  "holiday_flags": [0,0,0,0,0,0,0]
}
```

**Field Requirements:**

| Field | Type | Required | Valid Values | Notes |
|-------|------|----------|--------------|-------|
| weather_forecast | array[string] | YES | Exactly 7 values, each "Clear" or "Rainy" | Must have 7 items |
| holiday_flags | array[int] | YES | Exactly 7 values, each 0 or 1 | Must have 7 items |
| starting_date | string | YES | "YYYY-MM-DD" | Usually tomorrow's date |

**Success Response (200 OK):**
```json
{
  "success": true,
  "fallback": false,
  "forecast": [
    {
      "date": "2025-12-01",
      "day_name": "Monday",
      "day_number": 1,
      "predicted_demand": 38,
      "recommended_quantity": 40,
      "confidence": "High",
      "confidence_score": 0.85,
      "weather": "Clear",
      "is_holiday": "No",
      "is_new_item": false
    },
    {
      "date": "2025-12-02",
      "day_name": "Tuesday",
      "day_number": 2,
      "predicted_demand": 37,
      "recommended_quantity": 39,
      "confidence": "High",
      "confidence_score": 0.80,
      "weather": "Clear",
      "is_holiday": "No",
      "is_new_item": false
    }
    // ... 5 more days
  ]
}
```

**Backend Requirements:**
1. Get 7-day weather forecast from weather API
2. Check 7-day holiday calendar
3. Array lengths MUST be exactly 7, not 6 or 8
4. Store entire forecast array in database
5. If weather API fails, use ["Clear","Clear","Clear","Clear","Clear","Clear","Clear"]

**Mobile Requirements:**
1. Display as scrollable list or calendar view
2. Show confidence degradation (day 1 is High, day 7 is Low)
3. Use color coding for each day's confidence
4. Allow user to tap a day to see details

---

### 4. Waste Risk Alert

**Endpoint:** `POST /api/risk-alert`

**Purpose:** Check if planned quantity will cause waste. Shows red/yellow/green alert.

**Request Body:**
```json
{
  "predicted_demand": 42,
  "planned_quantity": 60
}
```

**Field Requirements:**

| Field | Type | Required | Valid Values |
|-------|------|----------|--------------|
| predicted_demand | int | YES | >= 0 |
| planned_quantity | int | YES | >= 0 |

**Success Response (200 OK - High Risk):**
```json
{
  "success": true,
  "risk_level": "HIGH",
  "waste_percentage": 30.0,
  "expected_waste": 18,
  "message": "High waste risk - reduce quantity.",
  "color": "red"
}
```

**Success Response (200 OK - Medium Risk):**
```json
{
  "success": true,
  "risk_level": "MEDIUM",
  "waste_percentage": 8.5,
  "expected_waste": 4,
  "message": "Moderate waste risk - consider reducing.",
  "color": "yellow"
}
```

**Success Response (200 OK - Low Risk):**
```json
{
  "success": true,
  "risk_level": "LOW",
  "waste_percentage": 2.3,
  "expected_waste": 1,
  "message": "Good planning - minimal waste expected.",
  "color": "green"
}
```

**Risk Calculation Logic:**
- waste_percentage = ((planned - predicted) / planned) * 100
- HIGH: waste_percentage > 15%
- MEDIUM: waste_percentage between 5% and 15%
- LOW: waste_percentage < 5%
- If planned_quantity = 0: returns LOW, waste_percentage = 0, message = "No production planned."

**Backend Requirements:**
1. Call this endpoint AFTER getting prediction
2. Call it again whenever user changes planned quantity
3. Store risk_level with the production plan
4. Log high-risk events for analytics

**Mobile Requirements:**
1. Show color-coded badge: red/yellow/green
2. Display message to user
3. Show expected_waste number: "You might waste 18 units"
4. Update in real-time as user adjusts quantity slider

---

### 5. Smart Recommendation

**Endpoint:** `POST /api/recommend`

**Purpose:** Tell user to REDUCE / INCREASE / MAINTAIN production quantity.

**Request Body:**
```json
{
  "predicted_demand": 40,
  "current_plan": 55
}
```

**Field Requirements:**

| Field | Type | Required | Valid Values |
|-------|------|----------|--------------|
| predicted_demand | int | YES | >= 0 |
| current_plan | int | YES | >= 0 (0 = user hasn't entered yet) |

**Success Response (200 OK - Reduce):**
```json
{
  "success": true,
  "recommended_quantity": 42,
  "action": "REDUCE by 13 units",
  "reason": "Current plan exceeds predicted demand - reducing avoids waste.",
  "explanation": "Predicted demand: 40 units. With 5% safety buffer -> recommend 42 units."
}
```

**Success Response (200 OK - Increase):**
```json
{
  "success": true,
  "recommended_quantity": 42,
  "action": "INCREASE by 7 units",
  "reason": "Current plan is below predicted demand - increasing avoids stockouts.",
  "explanation": "Predicted demand: 40 units. With 5% safety buffer -> recommend 42 units."
}
```

**Success Response (200 OK - Maintain):**
```json
{
  "success": true,
  "recommended_quantity": 42,
  "action": "MAINTAIN current plan",
  "reason": "Current plan is within the optimal range.",
  "explanation": "Predicted demand: 40 units. With 5% safety buffer -> recommend 42 units."
}
```

**Recommendation Logic:**
- recommended_quantity = round(predicted_demand * 1.05) (always includes 5% safety buffer)
- difference = recommended_quantity - current_plan
- if difference < -5: REDUCE
- if difference > 5: INCREASE
- else: MAINTAIN

**Backend Requirements:**
1. Call this after user enters planned quantity
2. Display the action prominently ("REDUCE by 13 units")
3. Show the reason in smaller text below
4. Auto-fill recommended_quantity in the input field (user can override)

**Mobile Requirements:**
1. Show action in bold with icon (down REDUCE, up INCREASE, check MAINTAIN)
2. Use colors: red for REDUCE, green for INCREASE, blue for MAINTAIN
3. Display reason text below action
4. Add "Auto-fill" button to set quantity to recommended_quantity

---

### 6. Model Accuracy Metrics

**Endpoint:** `POST /api/accuracy`

**Purpose:** Track how well the model is performing. Used for monitoring and deciding when to retrain.

**Request Body:**
```json
{
  "item_name": "Jollof Rice",
  "business_type": "Restaurant",
  "n_recent": 7
}
```

**Field Requirements:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| item_name | string | NO | Filter by item (optional) |
| business_type | string | NO | Filter by business (optional) |
| n_recent | int | NO (default: 7) | Number of recent evaluations to average |

**Success Response (200 OK):**
```json
{
  "success": true,
  "period": "Last 7 evaluations",
  "avg_mape": 8.12,
  "avg_mae": 4.22,
  "avg_r2": 0.922,
  "degraded": false,
  "alert_message": null,
  "target_mape": 20.0,
  "meets_target": true,
  "history": [
    {
      "timestamp": "2026-02-20T06:00:00",
      "mape": 8.5,
      "mae": 4.3,
      "r2": 0.918,
      "business_type": "Restaurant",
      "item_name": "Jollof Rice"
    }
    // ... more entries
  ]
}
```

**No Data Response (200 OK):**
```json
{
  "success": true,
  "message": "No accuracy logs yet. They are written by monitoring.py after daily sales.",
  "metrics": null
}
```

**Accuracy Thresholds:**

| Flag | Triggers at | Action |
|------|-------------|--------|
| meets_target = false | avg_mape >= 20% | Alert and review |
| degraded = true | avg_mape > 25% | Consider retraining |

**Backend Requirements:**
1. Call this endpoint weekly to check model health
2. If degraded=true, notify admin
3. If meets_target=false (avg_mape >= 20%), trigger retraining alert
4. Log metrics to analytics dashboard

**DevOps Requirements:**
1. Set up alert on meets_target=false, not just degraded. The degraded flag only flips at 25%, not 20%
2. Monitor trend: if MAPE increasing for 3 consecutive weeks, flag for review

---

### 7. Trigger Retraining

**Endpoint:** `POST /api/retrain`

**Purpose:** Update model with new sales data. Run this monthly or when accuracy degrades.

**Request Body:**
```json
{
  "new_data_path": "/path/to/new_sales_data.csv"
}
```

**Field Requirements:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| new_data_path | string | YES | Absolute path to CSV file on server |

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Retraining started. Check /api/health and /api/accuracy for updates.",
  "data_path": "/path/to/new_sales_data.csv"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": {
    "success": false,
    "error": "File not found: /path/to/new_sales_data.csv"
  }
}
```

**Backend Requirements:**
1. Collect daily sales data in same format as training data
2. Save as CSV with columns: business_type, item_name, date, price, shelf_life_hours, quantity_available, quantity_sold, customer_demand, waste_quantity, weather_condition, holiday_flag
3. Upload CSV to server
4. Call this endpoint with file path
5. Retraining runs in background (takes 5-10 minutes)
6. Check /api/accuracy after 15 minutes to see new metrics

**DevOps Requirements:**
1. Set up monthly cron job to trigger retraining
2. Monitor retraining logs for errors
3. Back up old model before deploying new one

---

## Data Models (JSON Schemas)

### Menu Item (Backend Database Schema)

```sql
CREATE TABLE menu_items (
    id SERIAL PRIMARY KEY,
    business_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    shelf_life_hours FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id)
);
```

**Fields required by the ML API:**

| Field | Notes |
|-------|-------|
| item_name | Case-sensitive -- store exactly as intended |
| price | Positive decimal |
| shelf_life_hours | Positive float e.g. 0.5, 4, 24 |
| business_type | Stored at business level, not item level |

### Daily Forecast (Backend Database Schema)

```sql
CREATE TABLE daily_forecasts (
    id SERIAL PRIMARY KEY,
    business_id INT NOT NULL,
    item_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_demand INT NOT NULL,
    recommended_quantity INT NOT NULL,
    confidence VARCHAR(10) NOT NULL,  -- "High", "Medium", or "Low"
    confidence_score DECIMAL(3,2) NOT NULL,  -- 0.00 to 1.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, item_id, forecast_date),
    FOREIGN KEY (business_id) REFERENCES businesses(id),
    FOREIGN KEY (item_id) REFERENCES menu_items(id)
);

CREATE INDEX idx_forecasts_date ON daily_forecasts(forecast_date);
CREATE INDEX idx_forecasts_business ON daily_forecasts(business_id);
```

### Production Plan (Backend Database Schema)

```sql
CREATE TABLE production_plans (
    id SERIAL PRIMARY KEY,
    business_id INT NOT NULL,
    item_id INT NOT NULL,
    plan_date DATE NOT NULL,
    predicted_demand INT NOT NULL,
    planned_quantity INT NOT NULL,
    risk_level VARCHAR(10) NOT NULL,  -- "HIGH", "MEDIUM", or "LOW"
    waste_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id),
    FOREIGN KEY (item_id) REFERENCES menu_items(id)
);
```

---

## Backend Requirements

### 1. Database Migrations (MUST DO)

Run these SQL scripts in order:

```sql
-- Step 1: Add ML fields to menu_items
ALTER TABLE menu_items ADD COLUMN shelf_life_hours FLOAT;

-- Step 2: Create forecasts table
CREATE TABLE daily_forecasts (
    id SERIAL PRIMARY KEY,
    business_id INT NOT NULL,
    item_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_demand INT NOT NULL,
    recommended_quantity INT NOT NULL,
    confidence VARCHAR(10) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, item_id, forecast_date)
);

CREATE INDEX idx_forecasts_date ON daily_forecasts(forecast_date);
```

### 2. API Service Class (MUST CREATE)

```python
# services/ml_api_service.py
import requests
import logging
from datetime import datetime, timedelta

class MLAPIService:
    def __init__(self, base_url="http://192.168.1.181:8502"):
        self.base_url = base_url
        self.timeout = 10
    
    def health_check(self):
        """Check if ML API is available."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except:
            return False
    
    def get_prediction(self, item, date=None, weather="Clear", is_holiday=0):
        """Get single-day prediction."""
        if date is None:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/predict",
                json={
                    "item_name": item["item_name"],
                    "business_type": item["business_type"],
                    "date": date,
                    "price": float(item["price"]),
                    "shelf_life_hours": float(item["shelf_life_hours"]),
                    "weather": weather,
                    "is_holiday": is_holiday
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"ML API error: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"ML API exception: {e}")
            return None
    
    def check_risk(self, predicted_demand, planned_quantity):
        """Check waste risk."""
        try:
            response = requests.post(
                f"{self.base_url}/api/risk-alert",
                json={
                    "predicted_demand": predicted_demand,
                    "planned_quantity": planned_quantity
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logging.error(f"Risk check error: {e}")
            return None
```

### 3. Required Endpoints (MUST CREATE)

**A. Generate Daily Forecasts (Cron Job Endpoint)**

```python
@app.post("/api/forecasts/generate-daily")
def generate_daily_forecasts(business_id: int):
    """
    Call this every morning at 6 AM.
    Generates predictions for all menu items for tomorrow.
    """
    ml = MLAPIService()
    
    # Check ML API health
    if not ml.health_check():
        return {"error": "ML API unavailable"}, 503
    
    # Get business and menu items
    business = db.get_business(business_id)
    items = db.get_menu_items(business_id)
    
    # Get tomorrow's conditions
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    weather = weather_api.get_forecast(business["location"], tomorrow)  # "Clear" or "Rainy"
    is_holiday = 1 if calendar_api.is_holiday(tomorrow) else 0
    
    forecasts = []
    for item in items:
        prediction = ml.get_prediction(item, tomorrow, weather, is_holiday)
        
        if prediction and prediction.get("success"):
            # Save to database
            db.save_forecast(
                business_id=business_id,
                item_id=item["id"],
                forecast_date=tomorrow,
                predicted_demand=prediction["predicted_demand"],
                recommended_quantity=prediction.get("recommended_quantity"),
                confidence=prediction["confidence"],
                confidence_score=prediction["confidence_score"]
            )
            
            forecasts.append(prediction)
    
    return {"success": True, "forecasts": forecasts}
```

**B. Get Today's Forecasts (Frontend Calls This)**

```python
@app.get("/api/forecasts/today")
def get_today_forecasts(business_id: int):
    """Frontend displays these predictions to user."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    forecasts = db.query("""
        SELECT 
            f.predicted_demand,
            f.recommended_quantity,
            f.confidence,
            m.item_name,
            m.id as item_id
        FROM daily_forecasts f
        JOIN menu_items m ON f.item_id = m.id
        WHERE f.business_id = ? AND f.forecast_date = ?
        ORDER BY m.item_name
    """, business_id, today)
    
    return {"success": True, "date": today, "forecasts": forecasts}
```

**C. Check Waste Risk (User Enters Quantity)**

```python
@app.post("/api/production/check-risk")
def check_production_risk(business_id: int, item_id: int, planned_quantity: int):
    """User enters planned quantity, backend checks waste risk."""
    ml = MLAPIService()
    
    # Get today's forecast
    today = datetime.now().strftime("%Y-%m-%d")
    forecast = db.get_forecast(business_id, item_id, today)
    
    if not forecast:
        return {"error": "No forecast available for today"}, 404
    
    # Check risk
    risk = ml.check_risk(forecast["predicted_demand"], planned_quantity)
    
    if not risk:
        return {"error": "ML API unavailable"}, 503
    
    # Save production plan with risk
    db.save_production_plan(
        business_id=business_id,
        item_id=item_id,
        plan_date=today,
        predicted_demand=forecast["predicted_demand"],
        planned_quantity=planned_quantity,
        risk_level=risk["risk_level"],
        waste_percentage=risk["waste_percentage"]
    )
    
    return risk
```

### 4. Cron Job Setup (MUST CONFIGURE)

```bash
# Add to crontab (runs every day at 6 AM)
0 6 * * * curl -X POST http://your-backend.com/api/forecasts/generate-daily?business_id=1
```

Or use Python scheduler:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: requests.post("http://localhost:8000/api/forecasts/generate-daily?business_id=1"),
    'cron',
    hour=6,
    minute=0
)
scheduler.start()
```

---

## Mobile App Requirements

### 1. API Service (MUST CREATE)

```swift
// MLAPIService.swift
import Foundation

class MLAPIService {
    static let shared = MLAPIService()
    let baseURL = "http://192.168.1.181:8502"  // Update with production URL
    
    func getPrediction(item: MenuItem, completion: @escaping (Result<Prediction, Error>) -> Void) {
        let url = URL(string: "\(baseURL)/api/predict")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10
        
        let body: [String: Any] = [
            "item_name": item.name,
            "business_type": item.businessType,
            "date": getTomorrowDate(),
            "price": item.price,
            "shelf_life_hours": item.shelfLifeHours,
            "weather": "Clear",  // Get from weather service
            "is_holiday": 0       // Get from calendar
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data", code: 0)))
                return
            }
            
            do {
                let prediction = try JSONDecoder().decode(Prediction.self, from: data)
                completion(.success(prediction))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    private func getTomorrowDate() -> String {
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: Date())!
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: tomorrow)
    }
}
```

### 2. Data Models (MUST CREATE)

```swift
// Prediction.swift
struct Prediction: Codable {
    let success: Bool
    let fallback: Bool?
    let predictedDemand: Int?
    let recommendedQuantity: Int?
    let confidence: String?
    let confidenceScore: Double?
    let explanation: String?
    
    enum CodingKeys: String, CodingKey {
        case success
        case fallback
        case predictedDemand = "predicted_demand"
        case recommendedQuantity = "recommended_quantity"
        case confidence
        case confidenceScore = "confidence_score"
        case explanation
    }
}

struct RiskAlert: Codable {
    let success: Bool
    let riskLevel: String
    let wastePercentage: Double
    let expectedWaste: Int
    let message: String
    let color: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case riskLevel = "risk_level"
        case wastePercentage = "waste_percentage"
        case expectedWaste = "expected_waste"
        case message
        case color
    }
}
```

### 3. UI Requirements (MUST IMPLEMENT)

**Forecast Display Screen:**
- Show list of all menu items with predictions
- Color-code confidence: High=green, Medium=yellow, Low=orange
- Display recommended_quantity prominently
- Show warning icon if fallback=true

**Production Planning Screen:**
- Input field for planned quantity
- Real-time risk indicator (updates as user types)
- Color-coded alert badge (red/yellow/green)
- Display waste_percentage and expected_waste
- "Use Recommended" button to auto-fill recommended_quantity

**Error Handling:**
- Network timeout: Show "Prediction unavailable, using cached data"
- API down: Show "Service temporarily unavailable"
- Never crash, always have fallback UI

---

## DevOps Requirements

### 1. Health Monitoring (MUST SET UP)

```bash
# Uptime check (runs every 5 minutes) -- checks status field, not HTTP code
*/5 * * * * curl -s http://192.168.1.181:8502/api/health | grep -q '"status": "healthy"' || echo "ML API DEGRADED" | mail -s "Alert" ops@preppal.com
```

Or use monitoring service like:
- UptimeRobot (free)
- Pingdom
- New Relic

### 2. Alerts (MUST CONFIGURE)

**Critical Alerts (Slack/Email immediately):**
- ML API status != "healthy" for > 5 minutes
- API returns 500 errors for > 10 consecutive requests
- Average response time > 10 seconds

**Warning Alerts (Daily digest):**
- Model accuracy meets_target=false (avg_mape >= 20%)
- Fallback responses > 10% of total requests
- API response time > 3 seconds

### 3. Logs to Monitor

```bash
# Check API logs
tail -f /var/log/preppal-ml-api.log

# Key metrics to track:
# - Request count per endpoint
# - Average response time
# - Error rate (4xx, 5xx)
# - Fallback response rate
# - Model prediction accuracy (from /api/accuracy)
```

### 4. Backup & Recovery (MUST PLAN)

**Model Files to Backup (Daily):**
- final_model_v3.pkl
- category_label_encoder.pkl
- business_label_encoder.pkl
- processed_data_with_features_v3.csv

**Disaster Recovery Plan:**
1. If API crashes, auto-restart with systemd or pm2
2. If model file corrupted, restore from yesterday's backup
3. If entire server down, have backup deployment URL ready
4. Backend should cache last 7 days of forecasts as fallback

---

## Error Handling

### Error Response Format

All endpoints return errors in this format:

```json
{
  "detail": {
    "success": false,
    "error": "Human-readable error message"
  }
}
```

### Common Errors and How to Handle

| Error | Code | Cause | Backend Action |
|-------|------|-------|----------------|
| Invalid business_type | 400 | Sent "restaurant" instead of "Restaurant" | Show validation error to user |
| Negative price | 400 | price = -10 | Validate input before sending |
| Missing required field | 400 | Didn't send shelf_life_hours | Check all required fields |
| Model unavailable | 200 + fallback=true | Model file missing | Use cached prediction |
| API timeout | N/A | Response > 10 seconds | Use yesterday's forecast |
| Network error | N/A | Server unreachable | Show "Service unavailable" |

### Fallback Strategy

```
1. Try ML API
2. If fails, use cached prediction from yesterday
3. If no cache, use business-type average (40 for restaurant, 50 for cafe, 60 for bakery)
4. If all fails, show "Prediction unavailable" but let user continue
```

---

## Testing Checklist

### Backend Testing

- [ ] Health check returns 200 with status field -- check status field not HTTP code
- [ ] Can get prediction for existing item
- [ ] Can get prediction for NEW item (not in training data)
- [ ] Prediction fails gracefully if API down
- [ ] Fallback with no cache -- recommended_quantity is absent and handled correctly
- [ ] 7-day forecast returns exactly 7 days
- [ ] Risk alert shows red/yellow/green correctly with correct message strings
- [ ] Recommendation gives REDUCE/INCREASE/MAINTAIN
- [ ] Daily forecast cron job runs at 6 AM
- [ ] Forecasts saved to database correctly
- [ ] Can retrieve today's forecasts
- [ ] Error responses don't crash app

### Mobile Testing

- [ ] Prediction API call works
- [ ] Loading indicator shows while waiting
- [ ] Confidence colors display correctly
- [ ] Fallback message shows when fallback=true
- [ ] App handles missing recommended_quantity in no-cache fallback gracefully
- [ ] Network timeout handled gracefully
- [ ] Risk alert colors (red/yellow/green) display
- [ ] "Use Recommended" button fills quantity
- [ ] App doesn't crash if API returns error

### DevOps Testing

- [ ] Health monitoring checks status field, not HTTP code
- [ ] Alerts trigger when status != "healthy"
- [ ] Accuracy alert fires when meets_target=false
- [ ] Logs being collected
- [ ] Backup system configured
- [ ] Can restore from backup
- [ ] API auto-restarts if crashed

---

## Contact for Issues

**ML API Owner:** Euodia Sam (Data Science Lead)

**For Integration Issues:**
- Backend integration problems -> Contact Euodia
- API response format questions -> Contact Euodia
- Model accuracy concerns -> Contact Euodia
- Deployment issues -> Contact DevOps + Euodia

**API Base URL Updates:**
Once deployed to production, update:
- Backend: Change MLAPIService base_url
- Mobile: Change MLAPIService baseURL
- DevOps: Update health check URL

---

**End of Specification**

Last Updated: February 23, 2026  
Version: 3.1  
Status: Production Ready
