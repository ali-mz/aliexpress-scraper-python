from selenium import webdriver
from datetime import datetime as date_time
import datetime
import pandas as pd
import json
import time
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

class AliexpressScrape():

    def __init__(self, config_dir) -> None:

        with open (config_dir, 'r') as f:
            config = json.load(f) 
        self.urls = config['aliexpress_product_urls']
        self.output_path = config['output_path']

        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)


    def create_firefox_driver(self):
        self.driver = webdriver.Firefox()
    
    def scrape_data(self):

        self.create_firefox_driver()

        self.data_all = {}
        for url_counter, url in enumerate(self.urls):
            self.data = {}

            self.data_all[url_counter] = {}
            self.data_all[url_counter]['url'] = url
            self.driver.get(url)
            time.sleep(3)

            # store
            self.get_store_data()

            # product
            self.get_product_data()

            # shipping
            self.get_shipping_data()

            self.data_all[url_counter]['data'] = self.data
        
        # store results
        output_file = os.path.join(self.output_path, 'output.json')
        with open(output_file, 'w') as f:
            json.dump(self.data_all, f)

        # close the driver
        self.driver.close()

    def get_store_data(self):
        # store container
        store_container = self.driver.find_elements_by_class_name('store-container')

        # store name
        self.data['store-name'] = store_container[0].find_element_by_class_name('store-name').text

        # store positive feedbacl
        self.data['store-positive-feedback'] = store_container[0].find_element_by_css_selector('span').text.split(' ')[0].split('%')[0]


    def get_product_data(self):
        # product container
        product_container = self.driver.find_elements_by_class_name('product-info')

        # product name
        self.data['product-name'] = product_container[0].find_elements_by_class_name('product-title')[0].text

        # product review
        self.data['product-rating-average'] = product_container[0].find_elements_by_class_name('product-reviewer')[0].find_elements_by_class_name('overview-rating')[0].text
        self.data['product-review-number'] = product_container[0].find_elements_by_class_name('product-reviewer')[0].find_elements_by_class_name('product-reviewer-reviews')[0].text.split(' ')[0]
        self.data['product-order-number'] = product_container[0].find_elements_by_class_name('product-reviewer')[0].find_elements_by_class_name('product-reviewer-sold')[0].text.split(' ')[0]

        # product price
        product_price_container = product_container[0].find_elements_by_class_name('product-price')
        self.data['product-price-min'] = float(product_price_container[0].find_elements_by_class_name('product-price-value')[0].text.split(' ')[1])
        self.data['product-price-max'] = float(product_price_container[0].find_elements_by_class_name('product-price-value')[0].text.split(' ')[-1])
        self.data['product-price-avg'] = (self.data['product-price-min'] + self.data['product-price-max'])/2
        self.data['product-currency'] = product_price_container[0].find_elements_by_class_name('product-price-value')[0].text.split(' ')[0].split('$')[0]

        # product wishlist
        self.data['product-wishlist-number'] = int(product_container[0].find_elements_by_class_name('add-wishlist')[0].text)


    def get_shipping_data(self):
        
        # product shipping
        try:
            self.driver.find_elements_by_class_name('product-shipping-info')[0].click()
            product_shipping_options_container = self.driver.find_elements_by_class_name('logistics')
            product_shipping_table_trs = product_shipping_options_container[0].find_elements_by_class_name('table-tr')
            # data['shipping'] = {}
            for counter, product_shipping_table_tr in enumerate(product_shipping_table_trs[1:]):
                    
                del_date = str(date_time.today().year) + ' ' +  product_shipping_table_tr.find_elements_by_class_name('time-cell')[0].text
                try:
                    del_date = date_time.strptime(del_date, '%Y %b %d').strftime('%Y-%m-%d')
                    self.data[f'shipping-{counter}-estimated-date'] = del_date

                    # calculate number of days
                    try:
                        del_time = str(date_time.today().year) + ' ' +  product_shipping_table_tr.find_elements_by_class_name('time-cell')[0].text
                        del_time = date_time.strptime(del_time, '%Y %b %d')
                        self.data[f'shipping-{counter}-estimated-days'] = (del_time - date_time.today()).days
                    except:
                        self.data[f'shipping-{counter}-estimated-days'] = 'NA'

                    # cost 
                    if 'FREE' in product_shipping_table_tr.find_elements_by_class_name('table-td')[2].text.upper():
                        self.data[f'shipping-{counter}-cost'] = 0
                    else:
                        self.data[f'shipping-{counter}-cost'] = product_shipping_table_tr.find_elements_by_class_name('table-td')[2].text.split(' ')[-1]
                    self.data[f'shipping-{counter}-tracking'] = 'N' if 'close' in product_shipping_table_tr.find_elements_by_class_name('table-td')[-2].find_elements_by_css_selector('i')[0].get_attribute('class') else 'Y'
                    self.data[f'shipping-{counter}-service-provider'] = product_shipping_table_tr.find_elements_by_class_name('service-name')[0].text
                except:
                    pass
        except:
            # close the shipping page
            # self.driver.find_elements_by_class_name('next-dialog-close')[0].click()
            # print(NameError)
            pass


if __name__=="__main__":

    aliexpress = AliexpressScrape(os.path.join(dir_path, 'config.json'))
    aliexpress.scrape_data()
