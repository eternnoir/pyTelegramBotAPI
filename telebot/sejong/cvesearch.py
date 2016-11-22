import requests
import re
import traceback

# import htmlparser 2.7 / 3.4
try:
    from html.parser import HTMLParser
except ImportError as ie:
    from HTMLParser import HTMLParser

# default credit cve list
SWEETCHIP_CVE = ['2014-1799', '2015-0037', '2015-1712',
                 '2015-1714', '2015-2447', '2016-1745']
SHC_CVE = ['2016-0789']


# exception handler decorator
def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except:
            print(traceback.format_exc())
            result = None
        finally:
            return result
    return wrapper


# HTMLParser wrapper
class HTMLWrapper(HTMLParser, object):
    pass


# CVE Parser from remote site
class CVEParser(HTMLWrapper):
    def __init__(self):
        self.option = ""
        self.report = {'vendor': [], 'vt_info': "", 'cvss': "", 'summary': "", 'credit': ""}
        super(CVEParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            # if option is cvss
            if ('class', 'cvssbox') in attrs:
                self.option = "cvss"

            # if option is summary
            if ('class', 'cvedetailssummary') in attrs:
                self.option = "summary"

        if tag == "span":
            # if option is vulnability type
            attrs = dict(attrs)
            if "class" in attrs.keys():
                if attrs['class'].startswith('vt_'):
                    self.option = "vt_info"

        if tag == "a":
            # if option is vendor
            for k, v in attrs:
                if k == "href" and v.startswith('/version/'):
                    mapper = dict(attrs)
                    self.report['vendor'].append(mapper['title'])

    def handle_data(self, data):
        if self.option != "":
            self.report[self.option] += data.replace('\n', '').replace('\t', '').strip()

            if len(self.report[self.option]) != 0:
                self.report[self.option] += " "

            self.option = ""


# result = CVESearch.search_by_number() use like
class CVESearch:
    @handle_exception
    def search_by_number(self, number):
        # if not valid cve number type ****(num)-****(num) => len(9)
        if not re.match(r'([0-9]{4}-[0-9]{4})', number) or len(number) != 9:
            return None

        url = "https://www.cvedetails.com/cve/CVE-{0}/".format(number)
        res = requests.get(url)

        c = CVEParser()
        c.feed(res.text)
        report = c.report
        del c

        # special code requested by @sweetchip
        if number in SWEETCHIP_CVE:
            report['credit'] = "sweetchip"

        if number in SHC_CVE:
            report['credit'] = "Seung-Hyun Cho"

        return report
