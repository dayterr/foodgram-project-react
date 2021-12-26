import io

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import filters, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config

from .filters import IngredientFilter, RecipeFilter
from .models import Ingredient, IngredientInRecipe, Recipe, ShoppingList, Tag
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializer import (FavouriteSerializer, IngredientSerializer, RecipeReadSerializer, RecipeWriteSerializer,
                         ShoppingListSerializer, TagSerializer)

rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/fonts')


class RecipeViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter
    queryset = Recipe.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filter_class = IngredientFilter
    pagination_class = None
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class ShoppingListViewSet(APIView):
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def post(self, request, recipe_id):
        author = request.user
        data = {
            'author': author.id,
            'recipe': recipe_id
        }
        serializer = ShoppingListSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, recipe_id):
        author = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        rec_exists = ShoppingList.objects.filter(author=author, recipe=recipe).delete()
        if rec_exists[0] == 0:
            return Response('Данного рецепта нет в Вашем списке покупок', status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavouriteViewSet(APIView):
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def post(self, request, recipe_id):
        author = request.user
        data = {
            'author': author.id,
            'recipe': recipe_id
        }
        serializer = FavouriteSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, recipe_id):
        author = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        rec_exists = FavouriteSerializer.objects.filter(author=author, recipe=recipe).delete()
        if rec_exists[0] == 0:
            return Response('Данного рецепта нет в Избранном', status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingList(APIView):
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get(self, request):
        the_list = {}
        shop_list = IngredientInRecipe.objects.filter(recipe__shop_recipes__author=request.user)
        for ingredient in shop_list:
            if ingredient.ingredient.name not in the_list:
                the_list[ingredient.ingredient.name] = [ingredient.amount,
                                                        ingredient.ingredient.measurement_unit]
            else:
                the_list[ingredient.ingredient.name][0] += ingredient.amount
        response = HttpResponse(content_type='application/pdf; charset=UTF-8')
        response['Content-Disposition'] = 'attachment; filename="spisok.pdf"'
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        textobject = p.beginText()
        textobject.setTextOrigin(inch, 2.5*inch)
        pdfmetrics.registerFont(TTFont('Roboto', 'Roboto-Regular.ttf'))
        textobject.setFont('Roboto', 14)
        for ingr, data in the_list.items():
            stroka = f'{ingr}: {data[0]} {data[1]}'
            textobject.textLine(stroka)
        p.drawText(textobject)
        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
