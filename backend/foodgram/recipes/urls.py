from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import DownloadShoppingList, FavouriteViewSet, IngredientViewSet, RecipeViewSet, ShoppingListViewSet, TagViewSet

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('recipes/download_shopping_cart/', DownloadShoppingList.as_view()),
    path('recipes/<int:recipe_id>/shopping_cart/', ShoppingListViewSet.as_view(),
         name='add_recipe_to_shopping_cart'),
    path('recipes/<int:recipe_id>/favorite/', FavouriteViewSet.as_view(),
         name='add_recipe_to_favorite'),
    path('', include(router_v1.urls)),
]
