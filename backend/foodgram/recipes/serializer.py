from django.shortcuts import get_object_or_404
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from .models import Favourite, Ingredient, IngredientInRecipe, Recipe, ShoppingList, Tag

from users.models import User, Subscribe



class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('name', 'measurement_unit'),
                message='Рецепт можно добавить в список покупок только один раз'
            ),
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient', queryset=Ingredient.objects.all())
    name = serializers.SlugRelatedField(read_only=True, source='ingredient',
                                        slug_field='name')
    measurement_unit = serializers.SlugRelatedField(read_only=True, source='ingredient',
                                                    slug_field='measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeReadSerializer(serializers.ModelSerializer):
    from users.serializer import UserSerializer
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        ing_list = obj.ings_in_recipe.all()
        return IngredientInRecipeSerializer(ing_list, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        author = request.user
        return Favourite.objects.filter(author=author, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        author = request.user
        return ShoppingList.objects.filter(author=author, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    from users.serializer import UserSerializer
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source='ings_in_recipe')
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = ('author', 'id', 'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time')

    def create(self, validated_data):
        ingredients = validated_data.pop('ings_in_recipe')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)

        for ingredient in ingredients:
            IngredientInRecipe.objects.create(recipe=recipe, ingredient=ingredient['ingredient'],
                                              amount=ingredient.get('amount'))
        recipe.tags.set(tags)
        return recipe


class FourFieldRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingListSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingList
        fields = ('author', 'recipe')
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('author', 'recipe'),
                message='Рецепт можно добавить в список покупок только один раз'
            ),
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        recipe = FourFieldRecipeSerializer(instance.recipe,
                                           context={'request': request}).data
        return recipe


class FavouriteSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favourite
        fields = ('author', 'recipe')
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=('author', 'recipe'),
                message='Рецепт можно добавить в Избранное только один раз'
            ),
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        recipe = FourFieldRecipeSerializer(instance.recipe,
                                           context={'request': request}).data
        return recipe
