from dataclasses import asdict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from fintech.controllers.users import UserController
from fintech.infrastructure.user_repository import DjangoUserRepository
from fintech.domain.exceptions import EmailIsRegistered, NotAValidUser, UserNotFound, NotParamsProvided

class UserView(APIView):
    def get(self, request, id=None):
        try:
            user = UserController(DjangoUserRepository())
            real_user = user.get_data({
                "id": id
            })
            return Response(asdict(real_user), status=status.HTTP_200_OK)
        except UserNotFound as e:
            return Response({
                "error": str(e),
            }, status=status.HTTP_404_NOT_FOUND)
        except NotParamsProvided as e:
            return Response({
                "error": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        

    def post(self, request):
        # Process the POST request data
        try:
            user = UserController(DjangoUserRepository())
            new_user = user.create_user(request.data)
            return Response(asdict(new_user), status=status.HTTP_201_CREATED)
        except EmailIsRegistered as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_409_CONFLICT)
        except NotAValidUser as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)