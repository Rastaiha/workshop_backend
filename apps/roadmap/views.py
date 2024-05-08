from rest_framework import status
from rest_framework.response import Response

from rest_framework.response import Response
from rest_framework.decorators import api_view

from apps.roadmap.models import Link
from apps.fsm.models import FSM
from apps.roadmap.serializers import LinkSerializer
from apps.roadmap.utils import _get_fsm_links, _get_player_taken_path


@api_view(["POST"])
def get_player_taken_path(request):
    player_id = request.data.get('player_id', None)
    taken_path: list[Link] = _get_player_taken_path(player_id)
    return Response(data=LinkSerializer(taken_path, many=True).data, status=status.HTTP_200_OK)


@api_view(["POST"])
def get_fsm_roadmap(request):
    fsm_id = request.data.get('fsm_id', None)
    fsm = FSM.get_fsm(fsm_id)
    fsm_links = _get_fsm_links(fsm_id)
    return Response(data={'first_state_name': fsm.first_state.name, 'links': LinkSerializer(fsm_links, many=True).data}, status=status.HTTP_200_OK)
