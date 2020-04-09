import requests
from django.core.cache import cache
import json
import logging
import time
import math

logger = logging.getLogger(__name__)
CERTS_CATALOG_URL = "https://docs.microsoft.com/api/contentbrowser/search/certifications" \
                    "?environment=prod" \
                    "&locale=en-us" \
                    "&facet=levels" \
                    "&facet=products" \
                    "&facet=resource_type" \
                    "&facet=roles" \
                    "&facet=type" \
                    "&%24filter=((products%2Fany(t%3A%20t%20eq%20%27azure%27)))" \
                    "&%24orderBy=last_modified%20desc" \
                    "&%24skip=0" \
                    "&%24top=30"
CERTS_CATALOG_CACHE_TIMEOUT = 60*60  # 1h


def get_certifications_catalog():
    # Check if previously cached -> if so return cached version
    cached_catalog = cache.get('catalog')
    if cached_catalog is not None:
        return json.loads(cached_catalog)

    # Retrieve catalog
    time_before = time.time()
    certs = []
    exams = []
    has_next = True
    next_url = CERTS_CATALOG_URL
    while has_next:
        content = requests.get(next_url).json()
        certs.extend(r for r in content["results"] if r["resource_type"] == "certification")
        exams.extend(r for r in content["results"] if r["resource_type"] == "examination")
        has_next = content["count"] > (len(certs) + len(exams))
        if has_next:
            next_url = content["@nextLink"]
    time_taken = time.time() - time_before
    logger.warning(f"Retrieved certifications catalog in {math.floor(time_taken*1000)} ms")

    # Map exam objects to certs (the existing exam objects don't have "title" nor "last_modified")
    for cert in certs:
        full_exam_objects = []
        for exam_preview in cert["exams"]:
            full_exam_objects.append(next(filter(lambda exam: exam["uid"] == exam_preview["uid"], exams)))
        # and override old exams previews
        cert["exams"] = full_exam_objects

    # Clean up some unnecessary keys
    for cert in certs:
        del cert["icon_url"]
        del cert["resource_type"]
        for exam in cert["exams"]:
            del exam["icon_url"]
            del exam["resource_type"]
            del exam["products"]  # are subset (or all) of cert's products
            del exam["roles"]  # same as cert
            del exam["levels"]  # same as cert

    catalog = {"certs": certs}

    # Save cleaned catalog in cache and return
    cache.set('catalog', json.dumps(catalog), timeout=CERTS_CATALOG_CACHE_TIMEOUT)
    return catalog
