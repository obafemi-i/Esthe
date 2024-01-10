import requests
from selectolax.parser import HTMLParser
import pandas as pd
import os, re

output = 'output.csv'
scraped_urls_file = 'scraped_urls.txt'

session = requests.Session()


def get_html(url):
    header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'}

    response = session.get(url, headers=header)
    html = HTMLParser(response.content)

    return html


def export_to_csv(ads: list):
    file_exists = os.path.isfile(output)

    output_df = pd.DataFrame(ads)

    if not file_exists:
        output_df.to_csv(output, index=False)  
    else:
        output_df.to_csv(output, mode='a', header=False, index=False)


def get_scraped_urls():
    try:
        with open(scraped_urls_file, 'r') as file:
            scraped_urls = set(file.read().splitlines())
    except FileNotFoundError:
        scraped_urls = set()

    return scraped_urls


def parse_attribute_error(html, selector):
    try:
        return html.css_first(selector).text().strip()
    except AttributeError:
        return None


def parse_product_info(html):
    products = html.css('div.etheme-product-grid-item')

    for product in products:
        product_link = product.css_first('h2.woocommerce-loop-product__title.etheme-product-grid-title a').attributes['href']
        image_link = product.css_first('img.attachment-medium_large.size-medium_large').attributes['data-origin-src']

        # to avoid scraping an already scraped product URL incase the scraper has to be restarted
        if product_link in get_scraped_urls():
            print(f"Skipping {product_link} as it has already been scraped.")
            continue

        
        content = get_html(product_link)

        name = parse_attribute_error(content, 'h1.product_title.entry-title')
        price = parse_attribute_error(content, 'p.price bdi').replace('EUR', '')
        color = parse_attribute_error(content, 'span.iconic-wlv-variations__selection')
        description = parse_attribute_error(content, 'div#tab-description')


        # remove whitespaces, tabs, newlines, carriage returns
        cleaned_description = re.sub(r'\s+', '', description)

        products_list = []

        products_dict = {
            'Name': name,
            'Price': price,
            'Color': color,
            'Image_link': image_link,
            'Product_link': product_link,
            'Description': cleaned_description
        }

        products_list.append(products_dict)

        export_to_csv(products_list)

        # Add the scraped URL to the set of scraped URLs
        get_scraped_urls().add(product_link)

        # Save the scraped URLs to the file
        with open(scraped_urls_file, 'a') as file:
            file.write(product_link + '\n')

            
        print(f'{product_link} succesfully scraped, moving on...')


def main():
    for x in range(2, 5):
        url = f'https://www.esthe.co.uk/shop/{x}/?'

        main_page = get_html(url)

        parse_product_info(main_page)


if __name__ == '__main__':
    main()
