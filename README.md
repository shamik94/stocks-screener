# <a name="_ukiswfnv144b"></a>**Stock Screener and VCP Detection Application**
## <a name="_r3hhnr2w223n"></a>**Overview**
This application is a stock screening and Volatility Contraction Pattern (VCP) detection tool built using Python, FastAPI, SQLAlchemy, and PostgreSQL. It screens stocks based on predefined criteria inspired by Mark Minervini's trend template and detects VCP patterns to identify potential trading opportunities.

-----
## <a name="_5cullxg3dclw"></a>**Features**
- **Stock Screening**: Filters stocks that meet specific technical criteria, such as moving averages and price performance relative to 52-week highs and lows.
- **VCP Detection**: Analyzes screened stocks to detect VCP patterns, considering price contractions and volume analysis.
- **RESTful API**: Provides endpoints to retrieve the list of screened stocks and stocks with detected VCP patterns.
- **Database Integration**: Uses PostgreSQL for data storage, with efficient queries and indexing for performance.
- **Logging**: Implements logging to monitor application progress and assist in debugging.
- **Docker Support**: Includes a Dockerfile for containerization and easy deployment.

-----
## <a name="_eye9c2wp93h2"></a>**Prerequisites**
- **Python 3.8 or higher**
- **PostgreSQL**: Ensure PostgreSQL is installed and a database is created.
- **Git** (optional): For cloning the repository.
-----
## <a name="_vbmh8cf3m555"></a>**Installation**
### <a name="_z9wyg7e4dqxx"></a>**1. Clone the Repository**


```
git clone git@github.com:shamik94/stocks-screener.git
cd stocks-screener
```

### <a name="_myr7e278az6w"></a>**2. Set Up a Virtual Environment (Optional)**

```
python -m venv venv
source venv/bin/activate  # On Windows use venv\Scripts\activate
```

### <a name="_4d557ebv5e7i"></a>**3. Install Dependencies**

```
pip install -r requirements.txt
```

-----
## <a name="_i4p04c3di1st"></a>**Configuration**
### <a name="_19e747h1tgzd"></a>**1. Database Configuration**
Update the database configuration in src/database/__init__.py:


```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    # Fallback to local settings if DATABASE_URL is not set
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'stockdata')
    DB_USER = os.environ.get('DB_USER', 'your_db_username')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_db_password')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

```

Alternatively, set the environment variables:
```
- DATABASE_URL or
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```
### <a name="_mb7yddxbgr29"></a>**2. Data Availability**
Ensure that the stock\_data table in your PostgreSQL database is populated with historical stock data, including:

- symbol
- date
- open
- high
- low
- close
- volume
- country (should be 'usa' for this application)
-----
## <a name="_ldglz417th9w"></a>**Running the Application**
### <a name="_ftd69gou2emx"></a>**1. Initialize the Database**
The application will automatically create the necessary tables upon startup if they do not exist.
### <a name="_rblngxowui6u"></a>**2. Run the Application**

```
python -m src.main
```

The application will:

- Initialize the database.
- Run the stock screening service.
- Run the VCP detection service.
- Start the FastAPI server on http://127.0.0.1:8000
### <a name="_n2td4qsmtdyd"></a>**3. Access the API Endpoints**
**Screened Stocks**: Retrieve the list of screened stocks.

```
GET http://127.0.0.1:8000/screened\_stocks
```
**VCP Stocks**: Retrieve the list of stocks with detected VCP patterns.
```
GET http://127.0.0.1:8000/vcp\_stocks
```
-----
## <a name="_m43colgply8v"></a>**API Endpoints**
### <a name="_c8nve3e2scnf"></a>**1. /screened\_stocks**
- **Method**: GET
- **Description**: Returns a list of stocks that meet the screening criteria.

**Response**:

```
{
    "screened\_stocks": [
      {
        "symbol": "AAPL",
        "country": "usa"
      },
      {
        "symbol": "MSFT",
        "country": "usa"
      }
      // ... more stocks
    ]
}
```

### <a name="_v83fmgmry8kk"></a>**2. /vcp\_stocks**
- **Method**: GET
- **Description**: Returns a list of stocks where VCP patterns have been detected.

**Response**:
```
{
  "vcp_stocks": [
    {
      "symbol": "AAPL",
      "stage": "EARLY",
      "detected_date": "2023-10-01T12:34:56.789Z"
    },
    {
      "symbol": "MSFT",
      "stage": "MATURE",
      "detected_date": "2023-10-01T12:35:10.123Z"
    }
  ]
}

```
-----
## <a name="_cg2n4apl493e"></a>**Docker**
### <a name="_kr88rkgriyvw"></a>**1. Build the Docker Image**
bash

Copy code

docker build -t stock\_app .

### <a name="_fvmrgrkkl61d"></a>**2. Run the Docker Container**

```
docker run -p 8000:8000 \
  -e DB_HOST=your_db_host \
  -e DB_PORT=your_db_port \
  -e DB_NAME=your_db_name \
  -e DB_USER=your_db_username \
  -e DB_PASSWORD=your_db_password \
  stock_app
```

Replace the environment variables with your actual database configuration.
### <a name="_cd5okrljb2mx"></a>**3. Access the Application**
The API endpoints will be available at http://localhost:8000.

-----
## <a name="_d9mwspc29ihp"></a>**Logging**
- The application uses the logging module to provide progress updates and assist in debugging.
- Logs are output to the console by default.

Adjust the logging level in the services (screener\_service.py, vcp\_service.py) by changing:
python
Copy code
logging.basicConfig(level=logging.INFO)

- To include more detailed logs, set the level to DEBUG.
-----
## <a name="_e605dmaacixp"></a>**Notes**
- **Data Loading**: The application assumes that the historical stock data is already available in the database. The data\_loader.py module is not used in this setup.
- **Country Variable**: The country variable is hardcoded to 'usa'. Ensure that the country field in your data matches this value.
- **Performance Optimization**: The services have been optimized to handle large datasets efficiently by fetching only necessary data and using database aggregations.
-----
## <a name="_mtdak4hxhksd"></a>**Testing**
- **Unit Tests**: Implement unit tests to verify the functionality of individual components.
- **Integration Tests**: Test the entire workflow to ensure that services interact correctly and the API endpoints return the expected data.
- **Performance Tests**: Monitor resource usage and response times when processing large datasets.
-----

## <a name="_lsqalxqc0n2o"></a>**License**
This project is licensed under the MIT License. See the LICENSE file for details.

-----
## <a name="_oqk0hy45z3h7"></a>**Acknowledgments**
- Inspired by Mark Minervini's trend template and VCP methodology.
- Utilizes open-source libraries and tools, including FastAPI, SQLAlchemy, and PostgreSQL.


