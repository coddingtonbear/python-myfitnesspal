from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from typing_extensions import Literal, TypedDict


class CommandDefinition(TypedDict):
    function: Callable
    description: str
    is_alias: bool
    aliases: List[str]


MyfitnesspalUserId = str


class GoalDisplayDict(TypedDict):
    id: str
    display_type: str
    nutrients: List[str]


class UnitPreferenceDict(TypedDict):
    energy: str
    weight: str
    distance: str
    height: str
    water: str


class DiaryPreferencesDict(TypedDict):
    default_foot_view: str
    meal_names: List[str]
    tracked_nutrients: List[str]


class UnitValueContainer(TypedDict):
    unit: str
    value: float


class GoalPreferencesDict(TypedDict):
    workouts_per_week: int
    weekly_workout_duration: int
    weekly_exercise_energy: UnitValueContainer
    weight_change_goal: UnitValueContainer
    weight_goal: UnitValueContainer
    diary_goal_display: str
    home_goal_display: str
    macro_goal_format: str


class LocationPreferencesDict(TypedDict):
    time_zone: str
    country_code: str
    locale: str
    postal_code: str
    state: str
    city: str


IsoDateStr = str


class AdminFlagDict(TypedDict):
    status: str
    has_changed_username: bool
    forgot_password_or_username: bool
    warnings: int
    strikes: int
    revoked_privileges: List


class AccountDict(TypedDict):
    created_at: IsoDateStr
    updated_at: IsoDateStr
    last_login: IsoDateStr
    valid_email: bool
    registration_source: str
    roles: List[str]
    admin_flags: AdminFlagDict


class SystemDataDict(TypedDict):
    login_streak: int
    unseen_notifications: int


Unknown = Any


class UserProfile(TypedDict):
    type: str
    starting_weight_date: str
    starting_weight: UnitValueContainer
    main_image_url: str
    main_image_id: Optional[Unknown]
    birthdate: str
    height: UnitValueContainer
    first_name: Optional[str]
    last_name: Optional[str]
    sex: Literal["M", "F"]
    activity_factor: str
    headline: Optional[str]
    about: Optional[str]
    why: Optional[str]
    inspirations: List


class UserMetadata(TypedDict):
    id: MyfitnesspalUserId
    username: str
    email: str
    goal_displays: List[GoalDisplayDict]
    unit_preferences: UnitPreferenceDict
    diary_preferences: DiaryPreferencesDict
    goal_preferences: GoalPreferencesDict
    location_preferences: LocationPreferencesDict
    account: AccountDict
    system_data: SystemDataDict
    step_sources: List
    profiles: List[UserProfile]


class AuthData(TypedDict):
    token_type: str
    access_token: str
    expires_in: int
    refresh_token: str
    user_id: MyfitnesspalUserId


NutritionDict = Dict[str, float]


class MealEntry(TypedDict):
    name: str
    nutrition_information: NutritionDict


class NoteDataDict(TypedDict):
    body: str
    type: str
    date: str


class FoodItemNutritionDict(TypedDict):
    calcium: float
    carbohydrates: float
    cholesterol: float
    fat: float
    fiber: float
    iron: float
    monounsaturated_fat: float
    polyunsaturated_fat: float
    potassium: float
    protein: float
    saturated_fat: float
    sodium: float
    sugar: float
    trans_fat: float
    vitamin_a: float
    vitamin_c: float


class ServingSizeDict(TypedDict):
    id: str
    nutrition_multiplier: float
    value: float
    unit: str
    index: int


class FoodItemDetailsResponse(TypedDict):
    description: str
    brand_name: Optional[str]
    verified: bool
    nutrition: FoodItemNutritionDict
    calories: float
    confirmations: int
    serving_sizes: List[ServingSizeDict]
