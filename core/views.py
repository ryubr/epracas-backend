from django.shortcuts import get_object_or_404

from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from core.models import Praca, Gestor, Agenda, ProcessoVinculacao

from .serializers import PracaSerializer, PracaListSerializer, PracaUploadSerializer
from .serializers import GestorSerializer
from .serializers import AgendaSerializer
from .serializers import ProcessoVinculacaoSerializer


class DefaultMixin(object):
    filter_backends = (
            filters.DjangoFilterBackend,
            filters.SearchFilter,
            )


class MultiSerializerViewSet(ModelViewSet):

    def get_serializer_class(self):
        if self.action in self.serializers:
            return self.serializers.get(
                    self.action,
                    self.serializers[self.action]
                    )
        else:
            return self.serializer_class


class PracaViewSet(DefaultMixin, MultiSerializerViewSet):

    serializer_class = PracaSerializer
    queryset = Praca.objects.all()
    search_fields = ('nome', 'municipio', 'uf')

    serializers = {
            'list': PracaListSerializer,
            }


class PracaUploadHeader(DefaultMixin, APIView):

    parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, pk):
        praca = get_object_or_404(Praca, pk=pk)
        praca.header_img = request.FILES['header_img']
        praca.clean_fields()
        praca.save()

        serializer = PracaUploadSerializer(
                praca,
                context={'request': request})
        return Response(serializer.data)


class GestorViewSet(ModelViewSet):
    queryset = Gestor.objects.all()
    serializer_class = GestorSerializer


class ProcessoViewSet(DefaultMixin, ModelViewSet):
    queryset = ProcessoVinculacao.objects.all()
    serializer_class = ProcessoVinculacaoSerializer
    search_fields = ('gestor',)


class AgendaViewSet(DefaultMixin, ModelViewSet):
    queryset = Agenda.objects.all()
    serializer_class = AgendaSerializer
    # lookup_field = 'id_pub'


class DistanceView(DefaultMixin, APIView):

    def post(self, request, latlong=None):
        latlong = (request.data['lat'], request.data['long'])
        distancias = sorted(
                [
                    (praca, praca.get_distance(latlong))
                    for praca in Praca.objects.all()
                ],
                key=lambda distancia: distancia[1]
                )
        pracas = []

        for i in distancias[:5]:
            praca = {
                    'id_pub': i[0].id_pub,
                    'url': i[0].get_absolute_url(),
                    'municipio': i[0].municipio,
                    'uf': i[0].uf,
                    'situacao_descricao': i[0].get_situacao_display(),
                    'modelo_descricao': i[0].get_modelo_display(),
                    'latlong': "{}, {}".format(i[0].lat, i[0].long),
                    'distancia': round(i[1], -2)
                    }
            pracas.append(praca)

        return Response(pracas)
