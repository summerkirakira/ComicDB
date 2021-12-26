import requests
from lxml import etree
from datetime import datetime
import uuid
import os


def e_hentai_crawler(url):
    my_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    html = requests.get(url, headers=my_header)

    dom = etree.HTML(html.text)
    title = dom.xpath('//h1[@id="gn"]/text()')[0]
    left_list = dom.xpath('//div[@id="gdd"]/table/*')
    for para in left_list:
        print(f'{para[0].text}')
    ehentai_info_dict = {}
    published = datetime.strptime(left_list[0][1].text, '%Y-%m-%d %H:%M')
    languages = left_list[3][1].text.strip()
    length = int(left_list[-2][1].text.replace(' pages', ''))
    ehentai_info_dict['favorited'] = left_list[-1][1].text
    rating = float(dom.xpath('//td[@id="rating_label"]')[0].text.replace('Average: ', ''))
    tag_list = dom.xpath('//div[@id="taglist"]/table/*')
    tag_dict = {}
    for tag in tag_list:
        tag_name = tag[0].text[:-1]
        tag_content = []
        for content in tag[1]:
            tag_content.append(content[0].text)
        tag_dict[tag_name] = tag_content
    if 'artist' in tag_dict:
        author = tag_dict['artist']

    cover_url = dom.xpath('//div[@id="gd1"]/div/@style')[0].split(' ')[-2][4:-1]

    cover_img = requests.get(cover_url, headers=my_header)

    # cover_uuid = str(uuid.uuid1())
    # cover_url =
    #
    # with open(os.path.join('data', 'cover', f"{cover_uuid}.{cover_url.split('.')[-1]}"), 'wb') as f:
    #     f.write(cover_img.content)
    return {
        'title': title,
        'published': published,
        'languages': languages,
        'rating': rating,
        'cover': cover_url,
        'source': url,
        'author': author
    }


e_hentai_crawler('https://e-hentai.org/g/2095474/af5bbf65fd/')
pass
