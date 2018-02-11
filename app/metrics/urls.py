import prometheus_client
from django.conf.urls import url
from django.http import HttpResponse


def ExportToDjangoView(request):
    """Exports /metrics as a Django view.

    You can use django_prometheus.urls to map /metrics to this view.
    """
    registry = prometheus_client.REGISTRY
    metrics_page = prometheus_client.generate_latest(registry)
    return HttpResponse(
        metrics_page,
        content_type=prometheus_client.CONTENT_TYPE_LATEST)


urlpatterns = [
    url(r'^$', ExportToDjangoView,
        name='prometheus-metrics'),
]
