from .certifications_catalog import get_certifications_catalog
from django.core.cache import cache
import json
import requests
import urllib.parse
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)
EXAM_DETAILS_CACHE_TIMEOUT = 60*60  # 1h


def get_exam_details(uid):
    catalog = get_certifications_catalog()
    exam_url = None
    for cert in catalog["certs"]:
        for exam in cert["exams"]:
            if exam["uid"] == uid:
                exam_url = exam["url"]
                break
        if exam_url is not None:
            break

    # Handle missing exam
    if exam_url is None:
        logger.error(f"Sought exam uid '{uid}' was not found in catalog")
        return None

    # Check if previously cached -> if so return cached version
    cached_cert_details = cache.get(f'exam-{uid}')
    if cached_cert_details is not None:
        return json.loads(cached_cert_details)

    # Retrieve details
    r = requests.get(urllib.parse.urljoin("https://docs.microsoft.com/en-us/", exam_url))
    html = BeautifulSoup(r.content, "html.parser")
    try:
        title = _get_title(html)
        hilights = _get_summary_hilights(html)
        skills_measured_topics = _get_skills_measured_topics(html)
        skills_measured_outline_link = _get_skills_measured_link(html)
    except ValueError as e:
        logger.error(str(e))
        return None

    # Save cert details in cache and return
    exam_details = {
        "title": title,
        "hilights": hilights,
        "skills_measured": skills_measured_topics,
        "skills_measured_details": skills_measured_outline_link,
    }
    cache.set(f'exam-{uid}', json.dumps(exam_details), timeout=EXAM_DETAILS_CACHE_TIMEOUT)
    return exam_details

##
# Utils
##


def _get_title(html):
    # Seek element
    title_els = html.find_all(lambda tag: tag.name == "h1" and "Exam " in "".join(tag.strings) and ": " in "".join(tag.strings))
    if len(title_els) > 1:
        raise ValueError("Found multiple title elements")
    if not title_els:
        raise ValueError("Didn't find title element")
    # Seek content
    title = title_els[0].string
    if not title:
        raise ValueError("Title was empty")
    return title


def _get_summary_hilights(html):
    # Seek summary element
    summary_els = html.find_all("div", {"class": "summary"})
    if len(summary_els) > 1:
        raise ValueError("Found multiple summary elements")
    if not summary_els:
        raise ValueError("Didn't find summary element")
    # Seek any (optional) hilights
    hilight_els = summary_els[0].find_all("strong")
    hilight_parents = [el.parent for el in hilight_els if el.parent.strings]
    hilights_with_links = [
        {
            "content": "".join(el.strings),
            "links": [{"text": "".join(a.strings), "url": a["href"]} for a in el.find_all("a")]
        }
        for el in hilight_parents
    ]
    return hilights_with_links


def _get_skills_measured_topics(html):
    # Seek heading element (right before topics)
    heading_string = "Skills measured"
    heading_els = html.find_all("h2", string=heading_string)
    if len(heading_els) > 1:
        raise ValueError("Found multiple headings with text "+heading_string)
    if not heading_els:
        raise ValueError("Didn't find heading with "+heading_string)
    # Seek topics
    topics_el = heading_els[0].find_next_sibling("div")
    if not topics_el:
        raise ValueError("Didn't find next sibling containing actual 'skills measured' topics")
    # Filter out generic notes if exist (present in some pages, in some not)
    topics = [t for t in topics_el.stripped_strings if "This list is not definitive or exhaustive" not in t]
    return topics


def _get_skills_measured_link(html):
    # Seek element
    link_string = "skills outline"
    link_els = html.find_all(lambda tag: tag.name == "a" and link_string in "".join(tag.strings))
    if len(link_els) > 1:
        raise ValueError("Found multiple links with "+link_string)
    if not link_els:
        raise ValueError("Didn't find link with "+link_string)
    return link_els[0]["href"]
