"""Save scraped items into our database"""
import datetime
import logging

from tqdm import tqdm
from hubstorage import HubstorageClient

from manolo_scraper.models import db_connect
from manolo_scraper.settings import API_KEY
from manolo_scraper.settings import SH_PROJECT
from manolo_scraper.settings import SCRAPING_PAST_NUMBER_OF_DAYS

SPIDERS = [
    {
        "spider_name": "ambiente",
        "institution_name": "ambiente",
    },
    {
        "spider_name": "congreso",
        "institution_name": "congreso",
    },
    {
        "spider_name": "defensa",
        "institution_name": "defensa",
    },
    {
        "spider_name": "inpe",
        "institution_name": "inpe",
    },
    {
        "spider_name": "justicia",
        "institution_name": "justicia",
    },
    {
        "spider_name": "minagr",
        "institution_name": "minagr",
    },
    {
        "spider_name": "mincu",
        "institution_name": "mincu",
    },
    {
        "spider_name": "minedu",
        "institution_name": "minedu",
    },
    {
        "spider_name": "minem",
        "institution_name": "minem",
    },
    {
        "spider_name": "minsa",
        "institution_name": "minsa",
    },
    {
        "spider_name": "minvi",
        "institution_name": "vivienda",
    },
    {
        "spider_name": "mujer",
        "institution_name": "min. mujer",
    },
    {
        "spider_name": "osce",
        "institution_name": "osce",
    },
    {
        "spider_name": "pcm",
        "institution_name": "pcm",
    },
    {
        "spider_name": "presidencia",
        "institution_name": "presidencia",
    },
    {
        "spider_name": "produce",
        "institution_name": "produce",
    },
]


def fetch_and_save_items():
    hc = HubstorageClient(auth=API_KEY)
    project = hc.get_project(SH_PROJECT)
    for spider in SPIDERS:
        print("\nworking on spider {}".format(spider['spider_name']))
        spider_id = project.ids.spider(spider['spider_name'])
        summary = project.spiders.lastjobsummary(spiderid=spider_id)
        for element in summary:
            print(element['key'])
            job = hc.get_job(element['key'])
            items = job.items.iter_values()
            save_items(items, spider['institution_name'])


def save_items(items, institution):
    print("processing {}".format(institution))
    db = db_connect()
    today = datetime.datetime.today()
    earliest_date_to_search = today - datetime.timedelta(days=int(SCRAPING_PAST_NUMBER_OF_DAYS) * 2)
    sql_query = """
        SELECT sha1 FROM visitors_visitor
           WHERE institution='{0}'
           AND modified > '{1}'
    """.format(institution, earliest_date_to_search.date())
    hashes_in_db = [
        i['sha1']
        for i in db.query(sql_query)
    ]
    items_to_upload = []
    for item in tqdm(items):
        if item['sha1'] not in hashes_in_db:
            if '_type' in item:
                del item['_type']
            if '_key' in item:
                del item['_key']
            if 'title' not in item:
                item['title'] = ""
            if 'id_number' not in item:
                item['id_number'] = ""
            item['created'] = datetime.datetime.now()
            item['modified'] = datetime.datetime.now()
            item['date'] = datetime.datetime.strptime(item['date'], "%Y-%m-%d")
            items_to_upload.append(item)
            logging.info(
                "Saving: {0}, date: {1}".format(item['sha1'], item['date']))
        else:
            logging.info(
                "{0}, date: {1} is found in db, not saving".format(
                    item['sha1'],
                    item['date'],
                )
            )
    if items_to_upload:
        print("uploading {} items".format(len(items_to_upload)))
        table = db['visitors_visitor']
        table.insert_many(items_to_upload)
    else:
        print("nothing to upload to db")


def main():
    fetch_and_save_items()


if __name__ == "__main__":
    main()
