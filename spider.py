import csv
import json
import logging
import logging.config
import random
import re
import time

import numpy as np
import pandas as pd
import pymysql
import requests
import yaml


class JCRCrawler(object):
    def __init__(self):
        headers = 'headers.json'
        uas = 'user_agents.txt'
        logger = 'logging.yaml'
        self.headers, self.url1, self.payload1, self.url2, self.payload2 = self._load_headers(headers)
        self.uas = self._load_user_agents(uas)
        self.logger = self._get_logger(logger)

    def _get_logger(self, file):
        """
        Create a logger from the given YAML file.
        """
        with open(file, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            logger = logging.getLogger("simpleExample")

        return logger

    def _load_headers(self, file):
        """
        Deserialize the given JSON file to Python objects.
        """
        with open(file, 'r') as f:
            jsdict = json.load(f)
            headers = jsdict["headers"]
            url1 = jsdict["url1"]
            payload1 = jsdict["payload1"]
            url2 = jsdict["url2"]
            payload2 = jsdict["payload2"]

        return headers, url1, payload1, url2, payload2

    def _load_user_agents(self, file):
        """
        Load user-agents from the given TXT file.
        """
        uas = []
        with open(file, 'rb') as f:
            for ua in f.readlines():
                if ua:
                    uas.append(ua.strip()[:-1])
        random.shuffle(uas)

        return uas

    def _replace_user_agent(self, headers, uas):
        """
        Replace the user-agent in headers with a randomly chosen one from uas.
        """
        ua = random.choice(uas)
        headers['user-agent'] = ua

        return headers

    def _crawl_data(self, url, payload):
        """
        Crawl journal profile.
         Also recursively called to crawl journal ISO Abbreviation.
        """
        try:
            # headers = self._replace_user_agent(self.headers, self.uas)
            response = requests.session().post(url, data=payload, headers=self.headers)
            result = response.text
        except Exception as e:
            result = None
            self.logger.error('Crawl data exception: %s', e)

        return result

    def _parse_data(self, result, url, payload):
        """
        Parse journal profile and crawl its ISO Abbreviation based on the JCR Abbreviation.
        """
        if result is None:
            return None

        result_list = []
        try:
            content = json.loads(result)
            status = content['status'] if 'status' in content.keys() else False
            if status == 'Success':
                if 'data' in content.keys():
                    data = content['data']
                    for i in range(len(data)):
                        rank = data[i]['rank']
                        name = data[i]['journalName']
                        jcrAbbr = data[i]['abbrJournal']
                        issn = data[i]['issn'] if 'issn' in data[i].keys() else 'N/A'
                        eissn = data[i]['eissn'] if 'eissn' in data[i].keys() else 'N/A'
                        jif2019 = data[i]['jif2019'] if 'jif2019' in data[i].keys() else 'N/A'
                        jif5Years = data[i]['jif5Years'] if 'jif5Years' in data[i].keys() else 'N/A'
                        quartile = data[i]['quartile'] if 'quartile' in data[i].keys() else 'N/A'

                        payload = re.sub(r'"journal":.*,', '"journal":"{}",'.format(jcrAbbr), payload)
                        res = self._crawl_data(url, payload)
                        if res is None:
                            pass
                        info = json.loads(res)
                        status = info['status'] if 'status' in info.keys() else False
                        if status == 'Success':
                            if 'data' in info.keys():
                                profile = info['data']
                                isoAbbr = profile['isoAbbreviation'] if 'isoAbbreviation' in profile.keys() else 'N/A'
                                result_list.append([name, isoAbbr])
                else:
                    self.logger.info('No data now')
            else:
                self.logger.info("Status error")
        except Exception as e:
            self.logger.error('Parse data exception: %s', e)
        return result_list

    def _save_to_db(self, result_list):
        """
        Save journal abbreviation list to database.
        """
        if result_list is None:
            print('Nothing to save')
            return

        for item in result_list:
            name = item[0]
            isoAbbr = item[1]
            try:
                conn = pymysql.connect(host='localhost', user='root', password='root', database='jcr')
                cur = conn.cursor()
                sql = 'INSERT INTO journal_info (name, isoAbbr) VALUES ("{}", "{}")'.format(name, isoAbbr)
                cur.execute(sql)
                conn.commit()
            except Exception as e:
                self.logger.error('Save data exception: %s', e)

    def _save_to_csv(self, result_list):
        """
        Save journal abbreviation list in CSV format (using semicolons as separators
        in accordance with JebRef's abbreviation list requirements).
        """
        with open('journal_abbreviations.csv', 'a', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(result_list)

    def _drop_duplicates(self):
        """
        Drop duplicates in the CSV file and sort items by journal names.
        """
        file = 'journal_abbreviations.csv'
        pd.read_csv(file, delimiter=';', header=None)\
            .drop_duplicates()\
            .sort_values(by=0)\
            .to_csv(file, sep=';', header=None, index=False)

    def crawl(self):
        """
        Run the loop until no data crawled.
        """
        # offset = 1
        page = 1
        payload1 = json.dumps(self.payload1, separators=(',', ':'))
        payload2 = json.dumps(self.payload2, separators=(',', ':'))

        while True:
            offset = (page - 1) * 200 + 1
            time.sleep(np.random.rand() * 10)
            payload1 = re.sub(r'"start":\d+', '"start":{}'.format(offset), payload1)
            self.logger.info('Crawling page %s ...', page)
            result = self._crawl_data(self.url1, payload1)
            self.logger.info('Parsing page %s ...', page)
            result_list = self._parse_data(result, self.url2, payload2)
            if result_list is None or len(result_list) <= 0:
                break
            self.logger.info('Saving page %s ...', page)
            self._save_to_db(result_list)
            self._save_to_csv(result_list)
            # offset += 25
            page += 1

        self._drop_duplicates()


if __name__ == '__main__':
    JCRCrawler().crawl()
