from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView

class UserView(APIView):
    def get(self, request):
        return Response({"message": "Hello, World!"}, status=status.HTTP_200_OK)

    def post(self, request):
        # Process the POST request data
        return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)