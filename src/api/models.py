"""Data models for Camptocamp.org API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class LocaleContent(BaseModel):
    """Content in a specific language."""

    title: Optional[str] = None
    title_prefix: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    access: Optional[str] = None
    access_period: Optional[str] = None
    remarks: Optional[str] = None
    gear: Optional[str] = None
    external_resources: Optional[str] = None
    route_history: Optional[str] = None
    approach: Optional[str] = None
    descent: Optional[str] = None
    conditions: Optional[str] = None
    weather: Optional[str] = None
    snow_conditions: Optional[str] = None
    rock_conditions: Optional[str] = None
    ice_conditions: Optional[str] = None
    mixed_conditions: Optional[str] = None
    avalanche_conditions: Optional[str] = None
    glacier_conditions: Optional[str] = None
    river_conditions: Optional[str] = None
    sea_conditions: Optional[str] = None
    other_conditions: Optional[str] = None
    # Route-specific locale fields
    slope: Optional[str] = None
    slackline_anchor1: Optional[str] = None
    slackline_anchor2: Optional[str] = None
    version: Optional[int] = None
    lang: Optional[str] = None


class Locales(BaseModel):
    """Multilingual content for an item."""

    fr: Optional[LocaleContent] = None
    en: Optional[LocaleContent] = None
    de: Optional[LocaleContent] = None
    it: Optional[LocaleContent] = None
    es: Optional[LocaleContent] = None
    ca: Optional[LocaleContent] = None
    eu: Optional[LocaleContent] = None
    sl: Optional[LocaleContent] = None
    zh: Optional[LocaleContent] = None


class Area(BaseModel):
    """Geographic area information."""

    document_id: Optional[int] = None
    version: Optional[int] = None
    locales: Optional[List[LocaleContent]] = None
    area_type: Optional[str] = None
    available_langs: Optional[List[str]] = None
    protected: Optional[bool] = None
    type: Optional[str] = None


class Geometry(BaseModel):
    """Geographic coordinates and elevation."""

    lat: Optional[float] = None
    lon: Optional[float] = None
    elevation: Optional[int] = None
    elevation_confidence: Optional[str] = None
    # PostGIS geometry fields
    geom: Optional[str] = None
    has_geom_detail: Optional[bool] = None
    version: Optional[int] = None


class Route(BaseModel):
    """Climbing route information."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None
    geometry: Optional[Geometry] = None

    # Route-specific fields
    difficulty: Optional[str] = None
    difficulty_rating: Optional[str] = None
    exposure: Optional[str] = None
    orientation: Optional[str] = None
    height_diff_up: Optional[int] = None
    height_diff_down: Optional[int] = None
    length: Optional[int] = None
    duration: Optional[int] = None
    seasons: Optional[List[str]] = None
    activities: Optional[List[str]] = None

    # Climbing-specific fields
    climbing_outdoor_type: Optional[str] = None
    climbing_rating: Optional[str] = None
    climbing_rating_scale: Optional[str] = None
    climbing_rating_min: Optional[str] = None
    climbing_rating_max: Optional[str] = None
    climbing_rating_median: Optional[str] = None

    # Route characteristics
    route_type: Optional[str] = None
    route_length: Optional[int] = None
    route_duration: Optional[int] = None
    route_height_diff: Optional[int] = None
    route_orientation: Optional[str] = None
    route_exposure: Optional[str] = None

    # Safety and conditions
    snow_rating: Optional[str] = None
    ice_rating: Optional[str] = None
    mixed_rating: Optional[str] = None
    rock_free_rating: Optional[str] = None
    rock_aid_rating: Optional[str] = None
    rock_rating_min: Optional[str] = None
    rock_rating_max: Optional[str] = None
    rock_rating_median: Optional[str] = None

    # Access and logistics
    access_time: Optional[int] = None
    approach_time: Optional[int] = None
    descent_time: Optional[int] = None
    hut_time: Optional[int] = None
    bivouac_time: Optional[int] = None

    # Additional API fields from database models
    elevation_min: Optional[int] = None
    elevation_max: Optional[int] = None
    durations: Optional[List[str]] = None
    calculated_duration: Optional[float] = None
    height_diff_difficulties: Optional[int] = None
    orientations: Optional[List[str]] = None
    global_rating: Optional[str] = None
    engagement_rating: Optional[str] = None
    risk_rating: Optional[str] = None
    equipment_rating: Optional[str] = None
    exposition_rock_rating: Optional[str] = None
    rock_required_rating: Optional[str] = None
    aid_rating: Optional[str] = None
    public_transportation_rating: Optional[str] = None
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Additional route-specific fields from database
    difficulties_height: Optional[int] = None
    height_diff_access: Optional[int] = None
    route_types: Optional[List[str]] = None
    glacier_gear: Optional[str] = None
    configuration: Optional[List[str]] = None
    lift_access: Optional[bool] = None
    ski_rating: Optional[str] = None
    ski_exposition: Optional[str] = None
    labande_ski_rating: Optional[str] = None
    labande_global_rating: Optional[str] = None
    via_ferrata_rating: Optional[str] = None
    hiking_rating: Optional[str] = None
    hiking_mtb_exposition: Optional[str] = None
    snowshoe_rating: Optional[str] = None
    mtb_up_rating: Optional[str] = None
    mtb_down_rating: Optional[str] = None
    mtb_length_asphalt: Optional[int] = None
    mtb_length_trail: Optional[int] = None
    mtb_height_diff_portages: Optional[int] = None
    rock_types: Optional[List[str]] = None
    slackline_type: Optional[str] = None
    slackline_height: Optional[int] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class Waypoint(BaseModel):
    """Waypoint information (passes, peaks, huts, etc.)."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None
    geometry: Optional[Geometry] = None

    # Waypoint-specific fields
    waypoint_type: Optional[str] = None
    elevation: Optional[int] = None
    elevation_confidence: Optional[str] = None
    prominence: Optional[int] = None
    activities: Optional[List[str]] = None

    # Waypoint characteristics
    waypoint_type_main: Optional[str] = None
    waypoint_type_sub: Optional[str] = None
    waypoint_type_extra: Optional[str] = None

    # Access and logistics
    access_time: Optional[int] = None
    approach_time: Optional[int] = None
    descent_time: Optional[int] = None
    hut_time: Optional[int] = None
    bivouac_time: Optional[int] = None

    # Hut-specific fields (when waypoint_type includes hut)
    capacity: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hut_type: Optional[str] = None
    guardian: Optional[bool] = None
    guardian_period: Optional[str] = None

    # Peak-specific fields (when waypoint_type includes peak)
    peak_type: Optional[str] = None
    peak_rank: Optional[int] = None
    peak_rank_scale: Optional[str] = None

    # Pass-specific fields (when waypoint_type includes pass)
    pass_type: Optional[str] = None
    pass_difficulty: Optional[str] = None

    # Additional API fields from database models
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Additional waypoint-specific fields from database
    elevation_min: Optional[int] = None
    height_max: Optional[int] = None
    height_median: Optional[int] = None
    height_min: Optional[int] = None
    routes_quantity: Optional[int] = None
    climbing_outdoor_types: Optional[List[str]] = None
    climbing_indoor_types: Optional[List[str]] = None
    climbing_rating_max: Optional[str] = None
    climbing_rating_min: Optional[str] = None
    climbing_rating_median: Optional[str] = None
    equipment_ratings: Optional[List[str]] = None
    climbing_styles: Optional[List[str]] = None
    children_proof: Optional[str] = None
    rain_proof: Optional[str] = None
    orientations: Optional[List[str]] = None
    best_periods: Optional[List[str]] = None
    product_types: Optional[List[str]] = None
    length: Optional[int] = None
    slope: Optional[int] = None
    ground_types: Optional[List[str]] = None
    paragliding_rating: Optional[str] = None
    exposition_rating: Optional[str] = None
    rock_types: Optional[List[str]] = None
    weather_station_types: Optional[List[str]] = None
    maps_info: Optional[str] = None
    public_transportation_types: Optional[List[str]] = None
    public_transportation_rating: Optional[str] = None
    snow_clearance_rating: Optional[str] = None
    lift_access: Optional[bool] = None
    parking_fee: Optional[str] = None
    phone_custodian: Optional[str] = None
    custodianship: Optional[str] = None
    matress_unstaffed: Optional[bool] = None
    blanket_unstaffed: Optional[bool] = None
    gas_unstaffed: Optional[bool] = None
    heating_unstaffed: Optional[bool] = None
    capacity_staffed: Optional[int] = None
    slackline_types: Optional[List[str]] = None
    slackline_length_min: Optional[int] = None
    slackline_length_max: Optional[int] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class Summit(BaseModel):
    """Mountain summit information."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None
    geometry: Optional[Geometry] = None

    # Summit-specific fields
    elevation: Optional[int] = None
    elevation_confidence: Optional[str] = None
    prominence: Optional[int] = None
    activities: Optional[List[str]] = None

    # Summit characteristics
    summit_type: Optional[str] = None
    summit_rank: Optional[int] = None
    summit_rank_scale: Optional[str] = None

    # Additional API fields
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class Hut(BaseModel):
    """Mountain hut information."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None
    geometry: Optional[Geometry] = None

    # Hut-specific fields
    elevation: Optional[int] = None
    capacity: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    activities: Optional[List[str]] = None

    # Hut characteristics
    hut_type: Optional[str] = None
    guardian: Optional[bool] = None
    guardian_period: Optional[str] = None
    booking_required: Optional[bool] = None
    open_period: Optional[str] = None

    # Access and logistics
    access_time: Optional[int] = None
    approach_time: Optional[int] = None
    descent_time: Optional[int] = None
    hut_time: Optional[int] = None
    bivouac_time: Optional[int] = None

    # Additional API fields
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class Article(BaseModel):
    """Collaborative article information."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None

    # Article-specific fields
    article_type: Optional[str] = None
    activities: Optional[List[str]] = None

    # Additional API fields
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class ClimbingSite(BaseModel):
    """Climbing site information."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None
    geometry: Optional[Geometry] = None

    # Climbing site-specific fields
    activities: Optional[List[str]] = None
    climbing_type: Optional[str] = None
    climbing_rating_min: Optional[str] = None
    climbing_rating_max: Optional[str] = None
    climbing_rating_scale: Optional[str] = None

    # Additional API fields
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class Outing(BaseModel):
    """Trip report and personal experience information."""

    id: int
    title: str
    summary: Optional[str] = None
    locales: Optional[Locales] = None
    geometry: Optional[Geometry] = None

    # Outing-specific fields
    outing_type: Optional[str] = None
    activities: Optional[List[str]] = None
    date: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None

    # Route and location information
    routes: Optional[List[int]] = None
    summits: Optional[List[int]] = None
    huts: Optional[List[int]] = None
    waypoints: Optional[List[int]] = None

    # Conditions and experience
    conditions: Optional[str] = None
    weather: Optional[str] = None
    snow_conditions: Optional[str] = None
    rock_conditions: Optional[str] = None
    ice_conditions: Optional[str] = None
    mixed_conditions: Optional[str] = None
    avalanche_conditions: Optional[str] = None
    glacier_conditions: Optional[str] = None
    river_conditions: Optional[str] = None
    sea_conditions: Optional[str] = None
    other_conditions: Optional[str] = None

    # Personal experience details
    participants: Optional[List[str]] = None
    duration: Optional[int] = None
    height_diff_up: Optional[int] = None
    height_diff_down: Optional[int] = None
    length: Optional[int] = None
    difficulty: Optional[str] = None
    exposure: Optional[str] = None

    # Photos and media
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None

    # Additional API fields
    available_langs: Optional[List[str]] = None
    areas: Optional[List[Area]] = None

    # Metadata
    url: Optional[str] = None
    license: Optional[str] = None
    quality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields from Camptocamp API
    document_id: Optional[int] = None
    version: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    protected: Optional[bool] = None
    redirects_to: Optional[int] = None
    redirects_to_document_id: Optional[int] = None


class CamptocampItem(BaseModel):
    """Wrapper for any Camptocamp content item."""

    item_type: str
    data: Union[Route, Waypoint, Summit, Hut, Article, ClimbingSite, Outing]
    raw_response: Dict[str, Any]


class APIResponse(BaseModel):
    """Generic API response wrapper."""

    documents: List[Dict[str, Any]]
    total: Optional[int] = None
    offset: Optional[int] = None
    limit: Optional[int] = None


class CollectionStats(BaseModel):
    """Statistics about collected data."""

    total_items: int = 0
    routes: int = 0
    summits: int = 0
    huts: int = 0
    waypoints: int = 0
    articles: int = 0
    climbing_sites: int = 0
    outings: int = 0
    cc_by_sa_licensed: int = 0
    multilingual_content: int = 0
    items_with_coordinates: int = 0
    items_with_descriptions: int = 0
