# coding: utf-8

import json
import pytest

from datetime import date
from datetime import datetime

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from model_mommy import mommy

from authentication.tests.test_user import authentication

pytestmark = pytest.mark.django_db

agenda_list_url = reverse('atividades:agenda-list')


def test_return_200_OK_on_main_endpoint_url(client):
    """
    Testa a URL principal do endpoint e verifica
    o retorno a uma requisição
    """

    url_esperada = '/api/v1/atividades/'
    url_resolvida = reverse('atividades:agenda-list')
    assert url_resolvida == url_esperada

    response = client.get(agenda_list_url)
    assert response.status_code == status.HTTP_200_OK


def test_return_a_list_with_5_events(client):
    """
    Testa o retorno de uma lista com cinco eventos
    """

    mommy.make('Agenda', _quantity=5)

    response = client.get(agenda_list_url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 5


def test_return_event_properties(client):
    """
    Testa o retorno de determinadas propriedades de um Evento,
    que são: url, id_pub, praca_url, praca_id_pub, titulo, data_inicio,
    data_encerramento, horario_inicio, horario_encerramento, descricao e
    local.
    """

    fields = [
        'url',
        'id_pub',
        'praca',
        'titulo',
        'descricao',
        'justificativa',
        'tipo',
        # 'area',
        'espaco',
        # 'parceiros',
        # 'faixa_etaria',
        'publico',
        'territorio',
        'carga_horaria',
        'publico_esperado',
    ]

    evento = mommy.make('Agenda')

    response = client.get(
        reverse('atividades:agenda-detail', kwargs={'pk': evento.id_pub}))

    assert response.status_code == status.HTTP_200_OK
    for field in fields:
        assert field in response.data


def test_return_events_related_with_a_Praca(client):
    """
    Testa o retorno de uma lista de atividades especificas de uma determinada
    praça utilizando filtros na URL.
    """

    praca1 = mommy.make('Praca')
    praca2 = mommy.make('Praca')

    mommy.make('Agenda', praca=praca1)

    response = client.get(
        reverse('atividades:agenda-list') + '?praca={}'.format(praca1.id_pub))

    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]['praca'] == praca1.id_pub


def test_get_all_ocurrances_from_a_month(client):
    """
    Testa a geração de todas as datas definidas através das datas de inicio
    e encerramento e a regra de repetição
    """

    event = mommy.make('Agenda')
    occurrence = mommy.make(
        'Ocorrencia',
        event=event,
        start=datetime(2010, 2, 12),
        end=datetime(2016, 2, 12),
        repeat='RRULE:FREQ=DAILY;INTERVAL=10;')

    response = client.get(
        reverse('atividades:agenda-list') + '?mes=3&ano=2012')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


def test_return_JSON_list_with_occurencies_from_an_event(client):
    """
    Testa o retorno de uma lista com as datas de ocorrencia de um determinado
    evento.
    """

    event = mommy.make('Agenda')
    occurrence = mommy.make(
        'Ocorrencia',
        event=event,
        start=datetime(2017, 2, 1),
        repeat_until=date(2017, 2, 15),
        frequency_type='daily',
        weekday='tu,th',
        )

    response = client.get(
        reverse('atividades:agenda-detail', kwargs={'pk': event.id_pub}),
        format='json')

    calendar = response.data.pop('ocorrencia')
    assert len(calendar['calendar']) == 4


def test_create_an_event_with_occurences_using_POST(client):
    """
    Testa a cricao de um evento e o retorno da resposta utilizando POST
    """

    praca = mommy.make('Praca')
    data = json.dumps({
        'praca': str(praca.id_pub),
        'titulo': 'Festival Teste',
        'justificativa': 'Justo',
        'espaco': 1,
        'tipo': 1,
        'publico': 'Publico',
        'carga_horaria': 10,
        'publico_esperado': 100,
        'territorio': 1,
        'descricao': 'Evento para testes',
        'ocorrencia':
        {
            'start': '2017-01-01T00:00',
            'repeat_until': '2017-01-23',
            'frequency_type': 'weekly'
        },
    })

    response = client.post(
        reverse('atividades:agenda-list'), data=data,
        content_type="application/json")

    assert response.status_code == status.HTTP_201_CREATED
    data = json.loads(data)
    assert data['praca'] in str(response.data['praca'])


def test_create_and_returning_a_list_of_dates(client):
    """
    Testa a criação de uma agenda via POST e o retorno de um calendario
    com as ocorrencias do evento
    """

    praca = mommy.make('Praca')
    data = json.dumps({
        'praca': str(praca.id_pub),
        'titulo': 'Festival Teste',
        'justificativa': 'Justo',
        'espaco': 1,
        'tipo': 1,
        'publico': 1,
        'carga_horaria': 10,
        'publico_esperado': 100,
        'territorio': 1,
        'descricao': 'Evento para testes',
        'ocorrencia': {
            'start': '2017-01-01T00:00',
            'repeat_until': '2017-01-07',
            'weekday': 'mo,fr',
            'frequency_type': 'daily',
        }
    })

    response = client.post(
        reverse('atividades:agenda-list'), data=data,
        content_type="application/json")

    assert response.status_code == status.HTTP_201_CREATED
    assert 'weekday' in response.data['ocorrencia']
    assert len(response.data['ocorrencia']['calendar']) == 2


@pytest.mark.skip
def test_closing_an_event_occurrence(authentication):

    client = APIClient()

    praca = mommy.make('Praca')
    ocorrencia = mommy.make('Agenda', praca=praca)

    request_data = {
        "relatorio": {
            "realizado": "true",
            "publico_presente": "100",
            "pontos_positivos": "Pontos Positivos",
            "pontos_negativos": "Pontos negativos",
        },
    }

    response = client.patch(
        reverse('atividades:agenda-detail', kwargs={'pk': ocorrencia.id_pub}),
        request_data,
        # content_type='application/json',
        format='json')

    assert response.status_code == status.HTTP_200_OK

    response = client.get(
        reverse('atividades:agenda-detail', kwargs={'pk': ocorrencia.id_pub}),
        format='json', )

    # import ipdb
    # ipdb.set_trace()
    assert response.status_code == status.HTTP_200_OK

    print(request_data)
    print(response.content)

    assert json.dumps(request_data) in str(response.content)


@pytest.mark.skip(reason="POST ainda não está implementado")
def test_submit_report_links_to_event(client):

    event = mommy.make('Agenda')

    request_body = {
        "data_de_ocorrencia": "04/12/1993",
        "realizado": "true",
        "publico_presente": "100",
        "pontos_positivos": "Evento ocorreu com tranquilidade",
        "pontos_negativos": "Nenhum ponto negativo"
    }

    response = client.post(
        reverse('atividades:agenda-detail', kwargs={'pk': event.id_pub}),
        data=request_body)

    assert json.dumps(request_body) in str(response.data)
