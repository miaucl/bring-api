"""Bring API types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal, NotRequired, TypedDict

from mashumaro import field_options
from mashumaro.config import TO_DICT_ADD_OMIT_NONE_FLAG
from mashumaro.mixins.orjson import DataClassORJSONMixin


class ActivityType(StrEnum):
    """Activity type."""

    LIST_ITEMS_CHANGED = "LIST_ITEMS_CHANGED"
    LIST_ITEMS_ADDED = "LIST_ITEMS_ADDED"
    LIST_ITEMS_REMOVED = "LIST_ITEMS_REMOVED"


class BringNotificationType(StrEnum):
    """Notification type.

    GOING_SHOPPING: "I'm going shopping! - Last chance for adjustments"
    CHANGED_LIST: "List changed - Check it out"
    SHOPPING_DONE: "Shopping done - you can relax"
    URGENT_MESSAGE: "Breaking news - Please get {itemName}!
    LIST_ACTIVITY_STREAM_REACTION: React with 🧐, 👍🏼, 🤤 or 💜 to activity
    """

    GOING_SHOPPING = "GOING_SHOPPING"
    CHANGED_LIST = "CHANGED_LIST"
    SHOPPING_DONE = "SHOPPING_DONE"
    URGENT_MESSAGE = "URGENT_MESSAGE"
    LIST_ACTIVITY_STREAM_REACTION = "LIST_ACTIVITY_STREAM_REACTION"


class ReactionType(StrEnum):
    """Activity reaction types."""

    THUMBS_UP = "THUMBS_UP"
    MONOCLE = "MONOCLE"
    DROOLING = "DROOLING"
    HEART = "HEART"


class BringItemOperation(StrEnum):
    """Operation to be be executed on list items."""

    ADD = "TO_PURCHASE"
    COMPLETE = "TO_RECENTLY"
    REMOVE = "REMOVE"
    ATTRIBUTE_UPDATE = "ATTRIBUTE_UPDATE"


class Status(StrEnum):
    """List status."""

    REGISTERED = "REGISTERED"
    UNREGISTERED = "UNREGISTERED"
    SHARED = "SHARED"
    INVITATION = "INVITATION"


class TemplateType(StrEnum):
    """Template or recipe."""

    TEMPLATE = "TEMPLATE"
    RECIPE = "RECIPE"
    POST = "POST"  # used for ads


@dataclass
class BaseModel(DataClassORJSONMixin):
    """Base model for Bring dataclasses."""

    class Config:
        """Config."""

        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]
        serialize_by_alias = True


@dataclass(kw_only=True)
class BringList(DataClassORJSONMixin):
    """A list class. Represents a single list."""

    listUuid: str
    name: str
    theme: str


@dataclass(kw_only=True)
class Content(DataClassORJSONMixin):
    """A content class. Represents a single item content."""

    urgent: bool
    convenient: bool
    discounted: bool


@dataclass(kw_only=True)
class Attribute(DataClassORJSONMixin):
    """An attribute class. Represents a single item attribute."""

    type: str
    content: Content


@dataclass(kw_only=True)
class BringPurchase(DataClassORJSONMixin):
    """A purchase class. Represents a single item."""

    uuid: str
    itemId: str
    specification: str
    attributes: list[Attribute] = field(default_factory=list)


@dataclass(kw_only=True)
class BringListItemDetails(DataClassORJSONMixin):
    """An item details class.

    Includes several details of an item in the context of a list.
    Caution: This does not have to be an item that is currently marked as 'to buy'.
    """

    uuid: str
    itemId: str
    listUuid: str
    userIconItemId: str
    userSectionId: str
    assignedTo: str
    imageUrl: str


@dataclass(kw_only=True)
class BringAuthResponse(DataClassORJSONMixin):
    """An auth response class."""

    uuid: str
    publicUuid: str
    bringListUUID: str
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    photoPath: str | None = None
    email: str | None = None
    name: str | None = None


@dataclass(kw_only=True)
class BringListResponse(DataClassORJSONMixin):
    """A list response class."""

    lists: list[BringList]


@dataclass(kw_only=True)
class Items(DataClassORJSONMixin):
    """An items class."""

    purchase: list[BringPurchase]
    recently: list[BringPurchase]


@dataclass(kw_only=True)
class BringItemsResponse(DataClassORJSONMixin):
    """An items response class."""

    uuid: str
    status: Status
    items: Items


@dataclass(kw_only=True)
class BringListItemsDetailsResponse(DataClassORJSONMixin):
    """A response class of a list of item details."""

    items: list[BringListItemDetails]


class ActivityReaction(TypedDict):
    """Reaction config."""

    moduleUuid: str
    moduleType: str
    reactionType: str


class BringNotificationsConfigType(TypedDict, total=True):
    """A notification config."""

    arguments: NotRequired[list[str]]
    listNotificationType: str
    senderPublicUserUuid: str
    receiverPublicUserUuid: NotRequired[str]
    listActivityStreamReaction: NotRequired[ActivityReaction]


@dataclass(kw_only=True)
class BringUserSettingsEntry(DataClassORJSONMixin):
    """A user settings class. Represents a single user setting."""

    key: str
    value: str


@dataclass(kw_only=True)
class BringUserListSettingEntry(DataClassORJSONMixin):
    """A user list settings class. Represents a single list setting."""

    listUuid: str
    usersettings: list[BringUserSettingsEntry]


@dataclass(kw_only=True)
class BringUserSettingsResponse(DataClassORJSONMixin):
    """A user settings response class."""

    usersettings: list[BringUserSettingsEntry]
    userlistsettings: list[BringUserListSettingEntry]


@dataclass(kw_only=True)
class UserLocale(DataClassORJSONMixin):
    """A user locale class."""

    language: str
    country: str


@dataclass(kw_only=True)
class PremiumConfiguration(DataClassORJSONMixin):
    """A premium configuration class."""

    hasPremium: bool
    hideSponsoredProducts: bool
    hideSponsoredTemplates: bool
    hideSponsoredPosts: bool
    hideSponsoredCategories: bool
    hideOffersOnMain: bool


@dataclass(kw_only=True)
class BringSyncCurrentUserResponse(DataClassORJSONMixin):
    """A sync current user response class."""

    email: str
    emailVerified: bool
    premiumConfiguration: dict[str, bool]
    publicUserUuid: str
    userLocale: UserLocale
    userUuid: str
    name: str | None = None
    photoPath: str | None = None


class BringAttribute(TypedDict):
    """An attribute dict. Represents a single item attribute."""

    type: str
    content: dict[str, bool]


class BringItem(TypedDict):
    """A BringItem."""

    itemId: str
    spec: str
    uuid: str | None
    operation: NotRequired[
        BringItemOperation
        | Literal[
            "TO_PURCHASE",
            "TO_RECENTLY",
            "REMOVE",
            "ATTRIBUTE_UPDATE",
        ]
    ]
    attribute: NotRequired[BringAttribute]


@dataclass(kw_only=True)
class BringAuthTokenResponse(DataClassORJSONMixin):
    """A refresh token response class."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass
class ActivityContent:
    """An activity content entry."""

    uuid: str
    sessionDate: datetime
    publicUserUuid: str
    items: list[BringPurchase] = field(default_factory=list)
    purchase: list[BringPurchase] = field(default_factory=list)
    recently: list[BringPurchase] = field(default_factory=list)


@dataclass
class Activity(DataClassORJSONMixin):
    """An activity entry."""

    type: ActivityType
    content: ActivityContent


@dataclass(kw_only=True)
class BringActivityResponse(DataClassORJSONMixin):
    """A list activity."""

    timeline: list[Activity] = field(default_factory=list)
    timestamp: datetime
    totalEvents: int


@dataclass(kw_only=True)
class BringErrorResponse(DataClassORJSONMixin):
    """Error resonse class."""

    message: str
    error: str
    error_description: str
    errorcode: int


@dataclass(kw_only=True)
class BringUser:
    """A Bring user."""

    publicUuid: str
    pushEnabled: bool
    plusTryOut: bool
    plusExpiry: datetime | None = None
    country: str = "CH"
    language: str = "de"
    name: str | None = None
    email: str | None = None
    photoPath: str | None = None


@dataclass(kw_only=True)
class BringUsersResponse(DataClassORJSONMixin):
    """List users."""

    users: list[BringUser] = field(default_factory=list)


@dataclass(kw_only=True)
class Ingredient(BaseModel):
    """Bring recipe ingredient."""

    itemId: str
    stock: bool
    spec: str | None = None
    altIcon: str | None = None
    altSection: str | None = None


@dataclass(kw_only=True)
class BringTemplate(BaseModel):
    """Bring recipe."""

    name: str | None = None
    author: str | None = None
    tagline: str | None = None
    linkOutUrl: str | None = None
    imageUrl: str | None = None
    imageWidth: int | None = None
    imageHeight: int | None = None
    items: list[Ingredient] = field(default_factory=list)
    requestQuantity: str | None = field(
        default=None, metadata=field_options(alias="yield")
    )
    baseQuantity: int | None = None
    time: str | None = None
    ingredients: list[Ingredient] = field(default_factory=list)
    likeCount: int | None = None
    tags: list[str] = field(default_factory=list)
    enableQuantityChange: bool | None = None
    uuid: str | None = None
    contentUuid: str | None = None
    contentVersion: int | None = None
    campaign: str | None = None
    title: str | None = None
    importCount: int | None = None
    template_type: TemplateType | None = field(
        default=TemplateType.TEMPLATE, metadata=field_options(alias="type")
    )
    isPromoted: bool | None = None
    isAd: bool | None = None
    contentSrcUrl: str | None = None
    attribution: str | None = None
    attributionSubtitle: str | None = None
    attributionIcon: str | None = None


@dataclass(kw_only=True)
class Inspiration(BaseModel):
    """Inspiration entry."""

    template_type: TemplateType | None = field(
        default=None, metadata=field_options(alias="type")
    )
    content: BringTemplate


@dataclass(kw_only=True)
class BringInspirationsResponse(BaseModel):
    """Bring inspirations response."""

    entries: list[Inspiration]
    count: int
    total: int


@dataclass(kw_only=True)
class InspirationFilter(BaseModel):
    """Inspiration filter."""

    id: str
    name: str
    isSpecial: bool
    tags: list[str]
    campaign: str
    isPromoted: bool
    isAd: bool
    backgroundColor: str | None = None
    foregroundColor: str | None = None
    imageUrl: str | None = None


@dataclass(kw_only=True)
class BringInspirationFiltersResponse(BaseModel):
    """Bring inspiration filters response."""

    filters: list[InspirationFilter]
