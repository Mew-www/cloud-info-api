from django.http.response import JsonResponse, HttpResponseNotFound
from azure.azure_api import AzureWebsiteInterface


def catalog_view(request):
    catalog = AzureWebsiteInterface.get_certifications_catalog()
    return JsonResponse(catalog)


def cert_details_view(request, cert_uid):
    cert_details = AzureWebsiteInterface.get_certification_details(cert_uid)
    if cert_details is None:
        return HttpResponseNotFound(f"Couldn't retrieve cert uid '{cert_uid}'")
    return JsonResponse(cert_details)


def exam_details_view(request, exam_uid):
    exam_details = AzureWebsiteInterface.get_exam_details(exam_uid)
    if exam_details is None:
        return HttpResponseNotFound(f"Couldn't retrieve exam uid '{exam_uid}'")
    return JsonResponse(exam_details)
