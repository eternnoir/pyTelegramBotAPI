import requests
import re

from html.parser import HTMLParser


# exception handler decorator
def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print("Exception! \n{0}".format(str(e)))
            result = "서버에서 오류가 발생하였습니다. 죄송합니다."
        finally:
            return result
    return wrapper


class CVEParser(HTMLParser):
    def initialize(self):
        self.option = ""
        self.report = {'vendor': [], 'vt_info': "", 'cvss': "", 'summary': ""}

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
            self.report[self.option] += data.replace('\n', '').replace('\t', '')

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
        c.initialize()
        c.feed(res.text)
        report = c.report
        del c

        report['cve'] = "CVE-{0}".format(number)
        report['url'] = "https://web.nvd.nist.gov/view/vuln/detail?"\
                        "vulnId=CVE-{0}".format(number)

        res = "CVE 검색 결과\n"
        res += "CVE 번호 : {0}\n".format(report['cve'])
        res += "CVSS : {0}\n".format(report['cvss'])

        vendors = " ".join(report['vendor'])
        res += "대상 벤더사 : {0}\n".format(vendors)

        res += "취약점 설명 : {0}\n".format(report['summary'])

        res += "취약점 분류 : {0}\n".format(report['vt_info'])
        res += "상세 링크 : {0}".format(report['url'])

        return res

result = CVESearch.search_by_number()
