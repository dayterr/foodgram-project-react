import django_filters

from .models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')
    author = django_filters.NumberFilter(field_name='author__id', lookup_expr='iexact')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('name', 'tags')
