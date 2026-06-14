# tests/plugins/test_semantic_category_resolver.py

from __future__ import annotations

import pytest

from backend.components.plugins.semantic_category_resolver.resolver import (
    KNOWN_SEMANTIC_TYPES,
    SemanticCategoryResolver,
)


@pytest.fixture
def resolver() -> SemanticCategoryResolver:
    return SemanticCategoryResolver()


class TestResolverBasic:
    """تست نگاشت‌های پایه."""

    def test_kababi_resolves_to_restaurant(self, resolver):
        assert resolver.resolve("کبابی های نزدیک میدان انقلاب") == "restaurant"

    def test_jigaraki_resolves_to_restaurant(self, resolver):
        assert resolver.resolve("جیگرکی اطراف میدان") == "restaurant"

    def test_sandwichi_resolves_to_restaurant(self, resolver):
        assert resolver.resolve("ساندویچی نزدیک رستوران مازو") == "restaurant"

    def test_pizza_resolves_to_restaurant(self, resolver):
        assert resolver.resolve("پیتزا فروشی اطراف میدان") == "restaurant"

    def test_abgooshti_resolves_to_restaurant(self, resolver):
        assert resolver.resolve("آبگوشتی نزدیک میدان") == "restaurant"

    def test_nonvaii_resolves_to_supermarket(self, resolver):
        assert resolver.resolve("نونوایی های اطراف میدان انقلاب") == "supermarket"

    def test_baghali_resolves_to_supermarket(self, resolver):
        assert resolver.resolve("بقالی نزدیک میدان انقلاب") == "supermarket"

    def test_sopri_resolves_to_supermarket(self, resolver):
        assert resolver.resolve("سوپری اطراف میدان") == "supermarket"

    def test_matab_resolves_to_clinic(self, resolver):
        assert resolver.resolve("مطب نزدیک میدان انقلاب") == "clinic"

    def test_kalanteri_resolves_to_police(self, resolver):
        assert resolver.resolve("کلانتری اطراف میدان") == "police"

    def test_mosaferkhaneh_resolves_to_hotel(self, resolver):
        assert resolver.resolve("مسافرخانه نزدیک میدان") == "hotel"

    def test_boostan_resolves_to_park(self, resolver):
        assert resolver.resolve("بوستان اطراف شهر") == "park"

    def test_emamzadeh_resolves_to_mosque(self, resolver):
        assert resolver.resolve("امامزاده نزدیک میدان") == "mosque"

    def test_daneshkadeh_resolves_to_university(self, resolver):
        assert resolver.resolve("دانشکده اطراف میدان") == "university"


class TestResolverNormalization:
    """تست نرمال‌سازی متن."""

    def test_zwnj_handling(self, resolver):
        assert resolver.resolve("کباب‌فروشی نزدیک میدان") == "restaurant"

    def test_extra_spaces(self, resolver):
        assert resolver.resolve("فست  فود  نزدیک  میدان") == "restaurant"

    def test_cng_latin(self, resolver):
        assert resolver.resolve("cng اطراف میدان") == "fuel"

    def test_atm_latin(self, resolver):
        assert resolver.resolve("atm نزدیک میدان انقلاب") == "atm"


class TestResolverFallback:
    """تست fallback برای semantic_typeهای ناموجود."""

    def test_bakery_fallback_to_supermarket(self, resolver):
        """نونوایی → bakery → supermarket چون bakery در داده نیست."""
        assert resolver.resolve("نانوایی اطراف میدان") == "supermarket"

    def test_unknown_returns_none(self, resolver):
        assert resolver.resolve("یک چیز عجیب غریب") is None

    def test_empty_text_returns_none(self, resolver):
        assert resolver.resolve("") is None


class TestResolverOutputValidity:
    """تست اینکه همه خروجی‌ها در KNOWN_SEMANTIC_TYPES باشند."""

    def test_all_results_are_known_types(self, resolver):
        test_inputs = [
            "کبابی", "ساندویچی", "نونوایی", "بقالی",
            "مطب", "کلانتری", "مسافرخانه", "بوستان", "جیگرکی",
            "دبستان", "حسینیه", "پاسگاه", "بنزین",
        ]
        for text in test_inputs:
            result = resolver.resolve(text)
            if result is not None:
                assert result in KNOWN_SEMANTIC_TYPES, (
                    f"'{text}' → '{result}' که در KNOWN_SEMANTIC_TYPES نیست"
                )


class TestOriginalCategoryMapIntact:
    """تست اینکه category_map اصلی دست‌نخورده است."""

    def test_original_pharmacy_still_works(self):
        from backend.components.parsers.category_map import detect_category
        assert detect_category("داروخانه نزدیک میدان") == "pharmacy"

    def test_original_bank_still_works(self):
        from backend.components.parsers.category_map import detect_category
        assert detect_category("بانک نزدیک میدان") == "bank"

    def test_original_restaurant_still_works(self):
        from backend.components.parsers.category_map import detect_category
        assert detect_category("رستوران نزدیک میدان") == "restaurant"
