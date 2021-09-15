import scrapy
from ..items import Mobile

class AmazonScraper(scrapy.Spider):
    name = "amazon_scraper"          ## name of the crawler

    # How many pages you want to scrape
    no_of_pages = 15

    # Headers to fix 503 service unavailable error
    # Spoof headers to force servers to think that request coming from browser ;)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.2840.71 Safari/539.36'}

    def start_requests(self):
        # starting urls for scraping
        urls = ["https://www.bgr.in/gadgets/mobile-phones/search/"]

        for url in urls: yield scrapy.Request(url = url, callback = self.parse, headers = self.headers)   ## call the parse function for crawl over the link 

    def parse(self, response):

        self.no_of_pages -= 1  # decrement the number of pages
       
        # get all the link mobile spec link as we have done in selenium
        mobiles = response.xpath("//li[@class='mobile-listing']//aside[@class='col-sm-12 col-lg-7 lstdesc']//h2//a").xpath("@href").getall()
        
        print("\n****\n",mobiles,"\n*****\n")
        ## iterate over each mobile spec link to scrap the specs 
        for mobile in mobiles:
            final_url = response.urljoin(mobile)
            yield scrapy.Request(url=final_url, callback = self.parse_mobile, headers = self.headers)      # call the parse_mobile function to scrap the specs
            

   
        
        if(self.no_of_pages > 0):
            ## get the url for the next page
            next_page_url = response.xpath("//ul[@class='pagination eventtracker']/li/a[@class='next pagination']").xpath("@href").get()
            final_url = response.urljoin(next_page_url)
            yield scrapy.Request(url = final_url, callback = self.parse, headers = self.headers)

    def parse_mobile(self, response):
        print("\n\n*************\n",response)
        ## get all the value in col 1 from the spec table as done selenium
        title = response.xpath("//section[@class='col-xs-12 blkSpecs']//ul//li//span[@class='col-xs-12 col-sm-5 spec-lbl']//text()").getall() 
        # scrap the name of the mobile phone
        name=response.xpath("//aside[@class='mobile-details-r']//h1[@itemprop='name']//text()").get() 
        ## get all the value in col 2 from the spec table as done selenium
        desc=response.xpath("//section[@class='col-xs-12 blkSpecs']//ul//li//span[@class='col-xs-12 col-sm-7 spec-val']//text()").getall() 
        
        info={}
        info['name']=name
        #scrap the price of mobile data 
        price=response.xpath("//aside[@class='mobile-details-r']//span[@class='rsm']//text()").get() 
        for k, val in zip(title, desc):
            info[k]=val
        print(info,"\n\n********\n\n")
        info['price']=price
        yield info     ## this would help to save the result
        
      