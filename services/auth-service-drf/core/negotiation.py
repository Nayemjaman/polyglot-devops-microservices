from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.renderers import JSONRenderer


class IgnoreClientContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        return parsers[0] if parsers else None

    def select_renderer(self, request, renderers, format_suffix=None):
        return JSONRenderer(), JSONRenderer.media_type
