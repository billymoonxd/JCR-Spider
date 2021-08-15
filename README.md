# JCR-Spider

Crawl journal ISO abbreviations from [JCR](https://jcr.clarivate.com/JCRLandingPageAction.action), which currently holds as many as 20,932 journals (as of August 2021).

The abbreviation list *journal_abbreviations.csv* can be used in place of JebRef's built-in list, which is not that satisfactory for me when generating journal ISO abbreviations.

## Debug 

It is required to set `x-1p-inc-sid` (authentication credentials) in the request header, otherwise you'll get [401 Unauthorized](https://httpstatuses.com/401).

It is tricky to deal with `cookie`, which contains `x-1p-inc-sid` in this case. The `CUSTOMER_NAME` leaks your organization information. It seems to work better without cookie.

Randomly choosing a `user-agent` from *user_agents.txt* did not lead to desired results. Choose the one in your Web browser is fine.

Letting the spider sleep for a while before crawling next page produced pleasing results. Yet, the application throws exceptions occasionally.

## Update

Certain fields may not exist in the response! Exceptions are thrown less frequently after adding the following statement:

```python
for i in range(len(data)):
	field = data[i]['field'] if 'field' in data[i].keys() else 'N/A'
```
However, the program got stuck when parsing page 457. 🤪

The `count` field (items per page) in the headers also makes a difference. A smaller one, say 25, makes requests about 5 times more frequently than when set to 200, in which case it is more likely to be blocked.

Yet I failed to crawl several pages even when requesting 200 items per page. To compensate, I'm just going to re-crawl missed pages from where it crashed (setting journal name as unique key to prevent duplicates).

## Result

After re-crawling 2 missed pages, I finally got 20,931 items. But I don't quite know why there is one item missing. 🤪

## To do list

- [ ] Toggle case

The journal abbreviation list contains a huge number of upper case words that are supposed to be capitalized, as well as acronyms and initialisms. Next I will capitalize these words while leaving those acronyms and initialisms as they are.

