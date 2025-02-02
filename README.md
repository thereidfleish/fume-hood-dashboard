# fume-hood-dashboard
### Overview of relevant folders/files
1. `dash` - folder containing Plotly Dash related files
    1. `assets` - folder containing the Dash css file
        1. `site.css` - main css file used to style the dashboard
    2. `pages` - folder containing python files for each of the dashboard pages
        1. `dashboard.py` - file representing the main fume hood dashboard page
    3. `app.py` - home page, file that you run to initialize the dashboard.  Right now just displays a 404 error.
2. `add_fumehood_data.ipynb` - code to process and add synthetic data to the database
3. `hoodnaming.ipynb` - csv file with Biotech raw point names and synthetic point names
4. Other files - irrelevant at this time

### Running the dashboard
1. Clone the repository
2. Install the latest version of the following packages (via pip or equivalent)
    1. `dash`
    2. `dash_bootstrap_components`
    3. `feffery-antd-components`
    4. `pandas`
    5. `numpy`
3. cd into the `dash` folder and run `python app.py`
    1. You should see something like `Dash is running on http://127.0.0.1:8055/` in the terminal.  Copy-paste this URL into a web browser to load the page.
        - If you get an error, you may not have all packages installed correctly.  Please reach out to rf377@cornell.edu for assistance.
    2. You will see a 404 page not found (this is expected).  Click the blue link above that text to enter the dashboard.
4. Alternately, use docker to run the dashboard server in a container. You will need to have docker installed to make this work.
    1. `docker build -t fume-hood-dashboard .`
    2. `docker run -dp 8055:8055 fume-hood-dashboard`
