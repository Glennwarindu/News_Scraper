# News Article Scraper

This project is a simple web scraper built with Scrapy. It collects news article information from several major news websites and saves the results into an Excel file.

If you are a beginner, this guide will help you run the scraper step by step.

## What this scraper does

The scraper:

- visits multiple news websites at the same time
- collects the article title, date, description, source URL, and source name
- saves everything into an Excel file

It works with news from:

- AP News
- Al Jazeera
- CNN
- BBC

## Before you start

Make sure you have:

- Python installed on your computer
- a terminal or command prompt open

## Step 1: Create the Scrapy project structure

A Scrapy project is the folder structure that holds your spider and settings.

To create it, run:

```bash
scrapy startproject spiderweb
```

This will create a project folder with files such as:

```bash
spiderweb/
├── scrapy.cfg
└── news/
    ├── __init__.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py
    └── spiders/
        └── news_scraper.py
```


Your spider file should be placed inside the spiders folder.

## Step 2: Create a virtual environment

A virtual environment keeps your project packages separate from the rest of your computer.

On Linux or Mac:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

After activation, your terminal should show the virtual environment name, such as (.venv).

## Step 3: Install the required packages

While your virtual environment is active, install the dependencies:

```bash
pip install -r requirements.txt
```

## Step 4: Run the scraper

From the project folder, run:

```bash
scrapy crawl news_scraper
```

This will start the spider and begin collecting news data.

## Step 5: Check the output

When the scraper finishes, it will create an Excel file in the project folder. The file name will look like this:

```bash
news_articles_YYYYMMDD_HHMMSS.xlsx
```

## Important note for beginners

Always run the scraper while your virtual environment is active.
If you close the terminal, you may need to activate the virtual environment again:

```bash
source .venv/bin/activate
```

## Project files

The main scraper logic is in the spider file inside the spiders folder.

The most important files are:

- scrapy.cfg: the Scrapy project configuration file
- settings.py: project settings
- items.py: the data structure for scraped items
- pipelines.py: saves the scraped data, including the Excel export
- spiders/news_scraper.py: the spider that does the actual crawling

## Troubleshooting

If you see an error, make sure:

- your virtual environment is active
- the required packages were installed correctly
- you are running the command from the project folder

If you want, you can also run the scraper with more detailed logs:

```bash
scrapy crawl news_scraper -s LOG_LEVEL=INFO
```
