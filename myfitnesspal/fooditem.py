from myfitnesspal.base import MFPBase


class FoodItem(MFPBase):
    def __init__(
        self,
        mfp_id,
        name,
        brand,
        verified,
        serving,
        calories,
        calcium=None,
        carbohydrates=None,
        cholesterol=None,
        fat=None,
        fiber=None,
        iron=None,
        monounsaturated_fat=None,
        polyunsaturated_fat=None,
        potassium=None,
        protein=None,
        saturated_fat=None,
        sodium=None,
        sugar=None,
        trans_fat=None,
        vitamin_a=None,
        vitamin_c=None,
        confirmations=None,
        servings=None,
    ):
        self._mfp_id = mfp_id
        self._name = name
        self._brand = brand
        self._verified = verified
        self._serving = serving
        self._calories = calories
        self._calcium = calcium
        self._carbohydrates = carbohydrates
        self._cholesterol = cholesterol
        self._fat = fat
        self._fiber = fiber
        self._iron = iron
        self._monounsaturated_fat = monounsaturated_fat
        self._polyunsaturated_fat = polyunsaturated_fat
        self._potassium = potassium
        self._protein = protein
        self._saturated_fat = saturated_fat
        self._sodium = sodium
        self._sugar = sugar
        self._trans_fat = trans_fat
        self._vitamin_a = vitamin_a
        self._vitamin_c = vitamin_c
        self._confirmations = confirmations
        self._servings = servings

    @property
    def mfp_id(self):
        return self._mfp_id

    @property
    def name(self):
        return self._name

    @property
    def brand(self):
        return self._brand

    @property
    def verified(self):
        return self._verified

    @property
    def serving(self):
        return self._serving

    @property
    def calories(self):
        return self._calories

    @property
    def calcium(self):
        return self._calcium

    @property
    def carbohydrates(self):
        return self._carbohydrates

    @property
    def cholesterol(self):
        return self._cholesterol

    @property
    def fat(self):
        return self._fat

    @property
    def fiber(self):
        return self._fiber

    @property
    def iron(self):
        return self._iron

    @property
    def monounsaturated_fat(self):
        return self._monounsaturated_fat

    @property
    def polyunsaturated_fat(self):
        return self._polyunsaturated_fat

    @property
    def potassium(self):
        return self._potassium

    @property
    def protein(self):
        return self._protein

    @property
    def saturated_fat(self):
        return self._saturated_fat

    @property
    def sodium(self):
        return self._sodium

    @property
    def sugar(self):
        return self._sugar

    @property
    def trans_fat(self):
        return self._trans_fat

    @property
    def vitamin_a(self):
        return self._vitamin_a

    @property
    def vitamin_c(self):
        return self._vitamin_c

    @property
    def confirmations(self):
        return self._confirmations

    @property
    def servings(self):
        return self._servings

    def __str__(self):
        return f"{self.name} -- {self.brand}"
