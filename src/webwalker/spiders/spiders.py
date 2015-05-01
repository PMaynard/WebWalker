"""

        A sample crawler for seeking a text on sites.

"""

import StringIO

from functools import partial

from scrapy.http import Request

from scrapy.spider import BaseSpider
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from scrapy.item import Item

import urllib2

def find_all_substrings(string, sub):
    """

http://code.activestate.com/recipes/499314-find-all-indices-of-a-substring-in-a-given-string/

    """
    import re
    starts = [match.start() for match in re.finditer(re.escape(sub), string)]
    return starts

class MySpider(CrawlSpider):
    """ Crawl through web sites you specify """

    name = "webwalker"

    # Stay within these domains when crawling
    allowed_domains = ["nakedsecurity.sophos.com"]

    start_urls = [
        "https://nakedsecurity.sophos.com"
    ]

    # Add our callback which will be called for every found link
    rules = [
        Rule(SgmlLinkExtractor(), follow=True, callback="check_violations")
    ]

    # How many pages crawled? XXX: Was not sure if CrawlSpider is a singleton class
    crawl_count = 0

    # How many text matches we have found
    violations = 0

    def get_pdf_text(self, response):
        """ Peek inside PDF to check possible violations.

        @return: PDF content as searcable plain-text string
        """

        try:
                from pyPdf import PdfFileReader
        except ImportError:
                print "Needed: easy_install pyPdf"
                raise 

        stream = StringIO.StringIO(response.body)
        reader = PdfFileReader(stream)

        text = u""

        if reader.getDocumentInfo().title:
                # Title is optional, may be None
                text += reader.getDocumentInfo().title

        for page in reader.pages:
                # XXX: Does handle unicode properly?
                text += page.extractText()

        return text                                      

    def check_violations(self, response):
        """ Check a server response page (file) for possible violations """

        # Do some user visible status reporting
        self.__class__.crawl_count += 1

        crawl_count = self.__class__.crawl_count
        if crawl_count % 100 == 0:
                # Print some progress output
                print "Crawled %d pages" % crawl_count

        # Entries which are not allowed to appear in content.
        # These are case-sensitive
        blacklist = ["SCADA", "ICS", "stuxnet", "havex"]

        # Enteries which are allowed to appear. They are usually
        # non-human visible data, like CSS classes, and may not be interesting business wise
        exceptions_after = [ "&",
                             "hamming",
                             "hamburg"
                     ]

        # These are predencing string where our match is allowed
        exceptions_before = [
                "POLIT", 
                "polit",
                "Tos",
                "tos"
        ]

        url = response.url

        # Check response content type to identify what kind of payload this link target is
        ct = response.headers.get("content-type", "").lower()
        if "pdf" in ct:
                # Assume a PDF file
                data = self.get_pdf_text(response)
        else:
                # Assume it's HTML
                data = response.body

        # Go through our search goals to identify any "bad" text on the page
        for tag in blacklist:

                substrings = find_all_substrings(data, tag)

                # Check entries against the exception list for "allowed" special cases
                for pos in substrings:
                        ok = False
                        for exception in exceptions_after:
                                sample = data[pos:pos+len(exception)]
                                if sample == exception:
                                        #print "Was whitelisted special case:" + sample
                                        ok = True
                                        break

                        for exception in exceptions_before:
                                sample = data[pos - len(exception) + len(tag): pos+len(tag) ]
                                #print "For %s got sample %s" % (exception, sample)
                                if sample == exception:
                                        #print "Was whitelisted special case:" + sample
                                        ok = True
                                        break
                        if not ok:
                                self.__class__.violations += 1
                                print "Violation number %d" % self.__class__.violations
                                print "URL %s" % url
                                print "Violating text:" + tag
                                print "Position:" + str(pos)
                                piece = data[pos-40:pos+40].encode("utf-8")
                                print "Sample text around position:" + piece.replace("\n", " ")
                                # Download.
                                html_str = urllib2.urlopen(url).read()
                                file = open('download/{0}/{1}.html'.format(tag, str(pos)), 'w')
                                file.write(html_str)
                                file.close()
                                print "Saved."
                                print "------"

        # We are not actually storing any data, return dummy item
        return Item()

    def _requests_to_follow(self, response):

        if getattr(response, "encoding", None) != None:
                # Server does not set encoding for binary files
                # Do not try to follow links in
                # binary data, as this will break Scrapy
                return CrawlSpider._requests_to_follow(self, response)
        else:
                return []