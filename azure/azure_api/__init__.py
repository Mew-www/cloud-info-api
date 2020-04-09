from .certifications_catalog import get_certifications_catalog
from .certification_details import get_certification_details
from .exam_details import get_exam_details
import logging

logger = logging.getLogger(__name__)


class AzureWebsiteInterface:
    def __init__(self):
        pass

    @staticmethod
    def get_certifications_catalog():
        return get_certifications_catalog()

    @staticmethod
    def get_certification_details(uid):
        return get_certification_details(uid)

    @staticmethod
    def get_exam_details(uid):
        return get_exam_details(uid)
