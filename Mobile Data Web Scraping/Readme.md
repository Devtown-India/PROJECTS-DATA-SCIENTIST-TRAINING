# Mobile Web Scraping 

We have use Selenium ,Beautifulsoup and Scrapy to extract the mobile phone data from [bgr](https://www.bgr.in/). Follow [here](https://medium.com/analytics-vidhya/scrapy-vs-selenium-vs-beautiful-soup-for-web-scraping-24008b6c87b8) for their comparision.

### Dependecies:
* [selenium](https://www.selenium.dev/)
* [chromedriver](https://chromedriver.chromium.org/)
* [scrapy](https://scrapy.org/)
* [scrapyjs](https://pypi.org/project/scrapyjs/)
* [bs4](https://pypi.org/project/bs4/)
* [request](https://pypi.org/project/requests/)


### Run scrapy on system:

```
cd mobile_scrapy && scrapy crawl amazon_scraper -o ../data/filename.csv
```


`explore.ipynb` contains the insight and visualization of scraped data. 