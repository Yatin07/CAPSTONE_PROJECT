# RestockIQ: Architecture & Design Diagrams (UML / Mermaid)

This document provides formal, publication-ready UML and architectural diagrams generated directly from the verified RestockIQ codebase for inclusion in Chapter 3 (System Design & Architecture) of the Capstone Project Black Book.

---

## 1. System Architecture Diagram

```mermaid
graph TB
    subgraph ClientLayer ["Client Layer (Mobile Front-End)"]
        FlutterApp["Flutter 3.38+ Mobile Application<br/>(Android 13 / ARM64)"]
        subgraph Providers ["Provider State Management"]
            InvProv["InventoryProvider"]
            AlertProv["WasteAlertsProvider"]
            StockProv["StockCheckProvider"]
            AuthProv["AuthProvider"]
        end
        FlutterApp --> Providers
    end

    subgraph APILayer ["Application & Routing Layer (Render Cloud)"]
        FastAPI["FastAPI High-Performance REST Gateway<br/>(Python 3.10 / Uvicorn / Docker)"]
        JWTAuth["JWT Bearer Authentication & Multi-Tenant Guard"]
        RateLimiter["IP Sliding-Window Rate Limiter<br/>(Reverse-Proxy Header Aware)"]
        GeminiService["Google Gemini RAG Service<br/>(gemini-3-flash-preview)"]
        
        FastAPI --> JWTAuth
        FastAPI --> RateLimiter
        FastAPI --> GeminiService
    end

    subgraph DatabaseLayer ["Persistence Layer (MongoDB Atlas Cloud)"]
        AtlasDB[("MongoDB Atlas Cloud Database<br/>(Cluster0 / M0 ReplicaSet)")]
        ColUsers[("Collection: users")]
        ColItems[("Collection: items")]
        ColForecasts[("Collection: forecasts")]
        ColIntraday[("Collection: intraday_sales")]
        
        AtlasDB --- ColUsers
        AtlasDB --- ColItems
        AtlasDB --- ColForecasts
        AtlasDB --- ColIntraday
    end

    subgraph BatchLayer ["Offline Machine Learning Engine (GitHub Actions Cron)"]
        NightlyBatch["Nightly Batch Daemon<br/>(ML/batch_forecast.py @ 02:00 UTC)"]
        ProphetEngine["Prophet Additive Seasonality Engine"]
        GBDTEngine["HistGradientBoostingRegressor (Residual Tree)"]
        NewsvendorEngine["Newsvendor Critical Ratio Module (z = +0.2533)"]
        TSBEngine["TSB Cold-Start Sparse Engine"]
        
        NightlyBatch --> ProphetEngine
        NightlyBatch --> GBDTEngine
        NightlyBatch --> NewsvendorEngine
        NightlyBatch --> TSBEngine
    end

    %% Interactions
    Providers -- "HTTPS / TLS 1.3 REST API (JSON)" --> FastAPI
    FastAPI -- "Async Motor Driver / Port 27017" --> AtlasDB
    NightlyBatch -- "Read Historical POS / Write Daily Predictions" --> AtlasDB
```

---

## 2. Entity-Relationship (ER) & Collections Diagram

```mermaid
erDiagram
    USERS ||--o{ ITEMS : "owns and manages"
    ITEMS ||--o{ FORECASTS : "has daily forecast"
    ITEMS ||--o{ INTRADAY_SALES : "records daily POS transactions"

    USERS {
        string _id PK
        string email UK "Unique indexed email"
        string password_hash "Bcrypt hashed password"
        string name "Store manager name"
        string role "owner | manager"
        string created_at "ISO-8601 UTC timestamp"
    }

    ITEMS {
        string _id PK
        string owner_id FK "Relational link to USERS._id"
        string name "Item title (e.g. Traditional Baguette)"
        string category "Bakery | Dairy | Beverage"
        string unit "Units | GAL | LBS"
        int currentStock "Real-time stock on hand"
        boolean isPerishable "True for fresh daily goods"
        float price "Retail price in EUR/USD"
        int predictedDemand "Nightly forecast value"
        int safetyStock "Buffer stock from Newsvendor policy"
        string riskLevel "normal | critical"
        string description "Grounded status text"
        boolean isDismissed "Alert dismissal flag"
        string updatedAt "ISO-8601 UTC timestamp"
    }

    FORECASTS {
        string _id PK
        string item_id FK "Relational link to ITEMS._id"
        string owner_id FK "Relational link to USERS._id"
        string forecast_date "Target calendar date (YYYY-MM-DD)"
        int predictedDemand "Point estimate demand"
        int safetyStock "Optimal buffer allowance"
        string riskLevel "normal | high | critical"
        string tier "primary | sparse_cold_start"
        array historical_7d "Trailing 7-day sales points"
        array forecast_7d "Next 7-day predicted points"
        null confidence_interval "Locked invariant: always null"
        string created_at "ISO-8601 timestamp"
    }

    INTRADAY_SALES {
        string _id PK
        string item_id FK "Relational link to ITEMS._id"
        string owner_id FK "Relational link to USERS._id"
        int quantity "Units sold at POS"
        string timestamp "ISO-8601 UTC event timestamp"
    }
```

---

## 3. End-to-End System Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Cron as GitHub Actions (02:00 UTC)
    participant Batch as ML Batch Engine (Python)
    participant Atlas as MongoDB Atlas Cloud
    participant API as FastAPI Cloud Gateway (Render)
    participant Client as Flutter Mobile App (Android)
    participant Gemini as Google Gemini AI Studio

    %% Phase 1: Nightly ML Batch
    Note over Cron,Atlas: Nightly Automated Forecasting Job (Past Closing Time)
    Cron->>Batch: Trigger nightly_forecast.yml cron
    Batch->>Atlas: Ingest 600-day sales history & current items
    Batch->>Batch: Execute Prophet & HistGradientBoosting Pipeline
    Batch->>Batch: Calculate Newsvendor Safety Stock (z = +0.2533)
    Batch->>Atlas: Batch upsert forecast documents into 'forecasts' collection
    Batch-->>Cron: Job complete (Exit code 0)

    %% Phase 2: Morning Manager Login & Dashboard
    Note over API,Client: Morning Shift Opening Walkthrough
    Client->>API: POST /api/v1/auth/login {email, password}
    API->>Atlas: Verify user & bcrypt hash in 'users'
    Atlas-->>API: User record verified
    API-->>Client: HTTP 200 OK (JWT Access Token)

    Client->>API: GET /api/v1/forecasts/today (Bearer Token)
    API->>Atlas: Fetch items & latest forecasts where owner_id = user_id
    Atlas-->>API: Active catalog + forecast records
    API-->>Client: HTTP 200 OK {summary, items, point-estimates}
    Client->>Client: Render Dashboard & Restock Steppers

    %% Phase 3: AI Natural Language Briefing
    Client->>API: GET /api/v1/briefing/today (Bearer Token)
    API->>Atlas: Read current inventory & waste alerts
    API->>Gemini: Synthesize daily summary prompt (Zero-Math Grounding)
    Gemini-->>API: Executive markdown narrative
    API-->>Client: HTTP 200 OK {briefing: "Today's priority is..."}
    Client->>Client: Display AI Briefing Card

    %% Phase 4: Intraday POS Logging & Waste Alerts
    Note over Client,API: Afternoon Operations (14:00 - 18:00)
    Client->>API: POST /api/v1/sales/intraday {item_id, quantity: 5}
    API->>Atlas: Insert transaction in 'intraday_sales'
    Client->>API: GET /api/v1/waste-alerts (Bearer Token)
    API->>API: Evaluate sales pace ratio (actual / expected)
    API-->>Client: HTTP 200 OK {alerts: [Traditional Baguette (Pace: 0.40)]}
    Client->>Client: Display Warning Card & "Apply 20% Discount" button
```

---

## 4. Use Case Diagram

```mermaid
graph LR
    subgraph Actors ["User Roles"]
        Manager(("Store Manager / Owner"))
        Cashier(("POS Cashier"))
        Baker(("Artisan Baker"))
    end

    subgraph UseCases ["RestockIQ System Use Cases"]
        UC1(["UC-01: Authenticate / Login"])
        UC2(["UC-02: View Daily Demand Dashboard"])
        UC3(["UC-03: Inspect Item Forecast & 7-Day Trend"])
        UC4(["UC-04: Execute One-Tap Reorder"])
        UC5(["UC-05: Record Intraday POS Sales"])
        UC6(["UC-06: Monitor Real-Time Waste Alerts"])
        UC7(["UC-07: Trigger Mitigation Markdown Action"])
        UC8(["UC-08: Query AI Operational Assistant"])
        UC9(["UC-09: Perform End-of-Day Inventory Check-In"])
        UC10(["UC-10: Manage Catalog Items (CRUD)"])
    end

    Manager --> UC1
    Manager --> UC2
    Manager --> UC3
    Manager --> UC4
    Manager --> UC6
    Manager --> UC7
    Manager --> UC8
    Manager --> UC9
    Manager --> UC10

    Cashier --> UC1
    Cashier --> UC5
    Cashier --> UC9

    Baker --> UC1
    Baker --> UC2
    Baker --> UC3
    Baker --> UC4
```

---

## 5. Detailed Class Diagram (Mapped from Actual Code Classes)

```mermaid
classDiagram
    %% Back-End Classes
    class UserDocument {
        +String _id
        +String email
        +String password_hash
        +String name
        +String role
        +String created_at
    }

    class ItemDocument {
        +String _id
        +String owner_id
        +String name
        +String category
        +String unit
        +int currentStock
        +bool isPerishable
        +float price
        +int predictedDemand
        +int safetyStock
        +String riskLevel
        +String description
        +bool isDismissed
        +String updatedAt
    }

    class ForecastDocument {
        +String _id
        +String item_id
        +String owner_id
        +String forecast_date
        +int predictedDemand
        +int safetyStock
        +String riskLevel
        +String tier
        +List historical_7d
        +List forecast_7d
        +null confidence_interval
    }

    class IntradaySaleDocument {
        +String _id
        +String item_id
        +String owner_id
        +int quantity
        +String timestamp
    }

    class WasteAlertTier {
        +String severityLabel
        +String severityColor
        +int discount_pct
        +String recommendedActionText
        +String primaryActionText
        +String layoutStyle
        +float salesPaceRatio
    }

    %% Front-End Classes
    class InventoryItem {
        +String id
        +String name
        +String category
        +String unit
        +int currentStock
        +bool isPerishable
        +double price
        +int predictedDemand
        +int safetyStock
        +int restockQuantity
        +double stockProgress
        +String riskLevel
        +computeRestockQuantity() int
    }

    class WasteAlertItem {
        +String id
        +String itemName
        +String salesText
        +double progress
        +double salesPaceRatio
        +String severityLabel
        +int discountPct
        +bool isPrimaryActionDone
        +bool isDismissed
    }

    class ApiService {
        -String _baseUrl
        -String _token
        +login(email, password) Future~bool~
        +getDashboardData() Future~DashboardData~
        +getWasteAlerts() Future~List~
        +applyDiscount(itemId) Future~bool~
        +askAssistant(query) Future~String~
    }

    class InventoryProvider {
        -List~InventoryItem~ _items
        -bool _isLoading
        +loadInventory() Future~void~
        +restockItem(id, qty) Future~void~
        +updateStock(id, newStock) void
    }

    class WasteAlertsProvider {
        -List~WasteAlertItem~ _alerts
        +loadAlerts() Future~void~
        +applyPrimaryAction(id) Future~void~
        +dismissAlert(id) Future~void~
    }

    %% Relationships
    UserDocument "1" -- "many" ItemDocument : owns
    ItemDocument "1" -- "many" ForecastDocument : generates
    ItemDocument "1" -- "many" IntradaySaleDocument : tracks
    WasteAlertTier <.. ItemDocument : evaluated by
    InventoryProvider --> ApiService : calls
    WasteAlertsProvider --> ApiService : calls
    InventoryProvider o-- InventoryItem : manages
    WasteAlertsProvider o-- WasteAlertItem : manages
```

---

## 6. Activity Diagram: Waste Alert & Markdown Mitigation Flow

```mermaid
flowchart TD
    Start([POS Sale Logged]) --> ReadStock[Fetch Current Item Stock & Sales Count]
    ReadStock --> CheckPerish{Is Item Perishable?}
    
    CheckPerish -- No --> Ignore[No Waste Alert Needed; Return Normal]
    CheckPerish -- Yes --> CalcElapsed[Calculate Day Elapsed Fraction<br/>elapsed = (CurrentHour - 8) / 12]
    
    CalcElapsed --> ExpectedSales[Compute Expected Sales by Now<br/>expected = daily_forecast * elapsed]
    ExpectedSales --> CalcRatio[Compute Sales Pace Ratio<br/>ratio = actual_sold / expected]
    
    CalcRatio --> EvaluateThreshold{Evaluate Ratio}
    
    EvaluateThreshold -- "ratio >= 0.70" --> NormalState[Normal Velocity: Low Risk<br/>No Action Required]
    EvaluateThreshold -- "0.35 <= ratio < 0.70" --> LowPaceAlert[Trigger Moderate Waste Alert<br/>Assign Medium Markdown]
    EvaluateThreshold -- "ratio < 0.35" --> CriticalAlert[Trigger High-Risk Spoilage Alert<br/>Assign Steep Markdown / Bundle]
    
    LowPaceAlert --> PushNotification[Display Alert Card on Mobile Dashboard]
    CriticalAlert --> PushNotification
    
    PushNotification --> ManagerDecision{Store Manager Action}
    
    ManagerDecision -- "Tap Apply Discount" --> UpdatePrice[POST /api/v1/waste-alerts/:id/apply-discount<br/>Update POS Price in Atlas]
    ManagerDecision -- "Tap Dismiss" --> MarkDismiss[POST /api/v1/waste-alerts/:id/dismiss<br/>Set isDismissed = True]
    ManagerDecision -- "No Action" --> WaitNextShift[Hold until next hourly check]
    
    UpdatePrice --> SuccessSnackbar[Show 'Discount Applied' Confirmation]
    MarkDismiss --> RemoveCard[Card Removed from View]
    
    SuccessSnackbar --> End([Flow Complete])
    RemoveCard --> End
    NormalState --> End
    Ignore --> End
    WaitNextShift --> End
```
