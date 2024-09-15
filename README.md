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
## <a name="_q7qflg9hk5x"></a>**Project Structure**
css

Copy code

project/

├── Dockerfile

├── requirements.txt

└── src/

`    `├── controller/

`    `│   ├── \_\_init\_\_.py

`    `│   └── api.py

`    `├── database/

`    `│   ├── \_\_init\_\_.py

`    `│   └── models.py

`    `├── main.py

`    `├── service/

`    `│   ├── \_\_init\_\_.py

`    `│   ├── screener\_service.py

`    `│   └── vcp\_service.py

-----
## <a name="_eye9c2wp93h2"></a>**Prerequisites**
- **Python 3.8 or higher**
- **PostgreSQL**: Ensure PostgreSQL is installed and a database is created.
- **Git** (optional): For cloning the repository.
-----
## <a name="_vbmh8cf3m555"></a>**Installation**
### <a name="_z9wyg7e4dqxx"></a>**1. Clone the Repository**
bash

Copy code

git clone git@github.com:shamik94/stocks-screener.git

cd stocks-screener

### <a name="_myr7e278az6w"></a>**2. Set Up a Virtual Environment (Optional)**
bash

Copy code

python -m venv venv

source venv/bin/activate  # On Windows use venv\Scripts\activate

### <a name="_4d557ebv5e7i"></a>**3. Install Dependencies**
bash

Copy code

pip install -r requirements.txt

-----
## <a name="_i4p04c3di1st"></a>**Configuration**
### <a name="_19e747h1tgzd"></a>**1. Database Configuration**
Update the database configuration in src/database/\_\_init\_\_.py:

python

Copy code

\# src/database/\_\_init\_\_.py

import os

from sqlalchemy import create\_engine

from sqlalchemy.orm import sessionmaker

from .models import Base

DATABASE\_URL = os.environ.get('DATABASE\_URL')

if not DATABASE\_URL:

`    `# Fallback to local settings if DATABASE\_URL is not set

`    `DB\_HOST = os.environ.get('DB\_HOST', 'localhost')

`    `DB\_PORT = os.environ.get('DB\_PORT', '5432')

`    `DB\_NAME = os.environ.get('DB\_NAME', 'stockdata')

`    `DB\_USER = os.environ.get('DB\_USER', 'your\_db\_username')

`    `DB\_PASSWORD = os.environ.get('DB\_PASSWORD', 'your\_db\_password')

`    `DATABASE\_URL = f"postgresql://{DB\_USER}:{DB\_PASSWORD}@{DB\_HOST}:{DB\_PORT}/{DB\_NAME}"

engine = create\_engine(DATABASE\_URL)

SessionLocal = sessionmaker(bind=engine)

Alternatively, set the environment variables:

- DATABASE\_URL or
- DB\_HOST, DB\_PORT, DB\_NAME, DB\_USER, DB\_PASSWORD
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
bash

Copy code

python -m src.main

The application will:

- Initialize the database.
- Run the stock screening service.
- Run the VCP detection service.
- Start the FastAPI server on http://127.0.0.1:8000
### <a name="_n2td4qsmtdyd"></a>**3. Access the API Endpoints**
**Screened Stocks**: Retrieve the list of screened stocks.
bash
Copy code
GET http://127.0.0.1:8000/screened\_stocks

**VCP Stocks**: Retrieve the list of stocks with detected VCP patterns.
bash
Copy code
GET http://127.0.0.1:8000/vcp\_stocks

-----
## <a name="_m43colgply8v"></a>**API Endpoints**
### <a name="_c8nve3e2scnf"></a>**1. /screened\_stocks**
- **Method**: GET
- **Description**: Returns a list of stocks that meet the screening criteria.

**Response**:
json
Copy code
{

`  `"screened\_stocks": [

`    `{

`      `"symbol": "AAPL",

`      `"country": "usa"

`    `},

`    `{

`      `"symbol": "MSFT",

`      `"country": "usa"

`    `}

`    `// ... more stocks

`  `]

}

### <a name="_v83fmgmry8kk"></a>**2. /vcp\_stocks**
- **Method**: GET
- **Description**: Returns a list of stocks where VCP patterns have been detected.

**Response**:
json
Copy code
{

`  `"vcp\_stocks": [

`    `{

`      `"symbol": "AAPL",

`      `"stage": "EARLY",

`      `"detected\_date": "2023-10-01T12:34:56.789Z"

`    `},

`    `{

`      `"symbol": "MSFT",

`      `"stage": "MATURE",

`      `"detected\_date": "2023-10-01T12:35:10.123Z"

`    `}

`    `// ... more stocks

`  `]

}

-----
## <a name="_cg2n4apl493e"></a>**Docker**
### <a name="_kr88rkgriyvw"></a>**1. Build the Docker Image**
bash

Copy code

docker build -t stock\_app .

### <a name="_fvmrgrkkl61d"></a>**2. Run the Docker Container**
bash

Copy code

docker run -p 8000:8000 \

`  `-e DB\_HOST=your\_db\_host \

`  `-e DB\_PORT=your\_db\_port \

`  `-e DB\_NAME=your\_db\_name \

`  `-e DB\_USER=your\_db\_username \

`  `-e DB\_PASSWORD=your\_db\_password \

`  `stock\_app

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
## <a name="_jr7i9koizzgs"></a>**Contributing**
Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

**Create a Feature Branch**
bash
Copy code
git checkout -b feature/your-feature-name

**Commit Your Changes**
bash
Copy code
git commit -am 'Add new feature'

**Push to the Branch**
bash
Copy code
git push origin feature/your-feature-name

1. **Create a Pull Request**
-----
## <a name="_lsqalxqc0n2o"></a>**License**
This project is licensed under the MIT License. See the LICENSE file for details.

-----
## <a name="_oqk0hy45z3h7"></a>**Acknowledgments**
- Inspired by Mark Minervini's trend template and VCP methodology.
- Utilizes open-source libraries and tools, including FastAPI, SQLAlchemy, and PostgreSQL.


