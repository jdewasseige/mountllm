"""Camptocamp.org API client for data collection."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import (
    APIResponse,
    Article,
    CamptocampItem,
    ClimbingSite,
    Hut,
    Outing,
    Route,
    Summit,
    Waypoint,
)


class CamptocampAPIError(Exception):
    """Custom exception for Camptocamp API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class CamptocampClient:
    """Client for interacting with Camptocamp.org API."""

    def __init__(
        self,
        base_url: str = "https://api.camptocamp.org",
        user_agent: str = "MountLLM-DataCollector/1.0",
        rate_limit: int = 100,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.request_count = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()

    async def _create_session(self):
        """Create aiohttp session with proper headers."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                    "Accept-Language": "en,fr;q=0.9",
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < 60.0 / self.rate_limit:
            sleep_time = (60.0 / self.rate_limit) - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited request to the API."""
        await self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        if params:
            url += "?" + urlencode(params)

        try:
            async with self.session.get(url) as response:
                if response.status == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise CamptocampAPIError("Rate limited", 429)

                if response.status != 200:
                    error_text = await response.text()
                    raise CamptocampAPIError(
                        f"API request failed with status {response.status}",
                        response.status,
                        error_text,
                    )

                return await response.json()

        except aiohttp.ClientError as e:
            raise CamptocampAPIError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise CamptocampAPIError(f"Invalid JSON response: {e}")

    def _extract_geometry(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract geometry information from API response."""
        geometry = {}

        # Check for different geometry formats
        if "geometry" in item:
            geom = item["geometry"]
            if isinstance(geom, dict) and "geom" in geom:
                # Parse PostGIS geometry string
                geom_str = geom["geom"]
                if geom_str.startswith("POINT(") and geom_str.endswith(")"):
                    coords = geom_str[6:-1].split()
                    if len(coords) >= 2:
                        geometry["lon"] = float(coords[0])
                        geometry["lat"] = float(coords[1])
                        if len(coords) >= 3:
                            geometry["elevation"] = int(float(coords[2]))

                # Enhanced GeoJSON parsing
                elif geom_str.startswith('{"type"') and geom_str.endswith("}"):
                    try:
                        import json

                        geom_json = json.loads(geom_str)
                        if (
                            geom_json.get("type") == "Point"
                            and "coordinates" in geom_json
                        ):
                            coords = geom_json["coordinates"]
                            if len(coords) >= 2:
                                geometry["lon"] = float(coords[0])
                                geometry["lat"] = float(coords[1])
                                if len(coords) >= 3:
                                    geometry["elevation"] = int(float(coords[2]))
                    except (json.JSONDecodeError, (ValueError, TypeError)):
                        pass

                # Store the original geom string and metadata
                geometry["geom"] = geom_str
                geometry["has_geom_detail"] = geom.get("has_geom_detail", False)
                geometry["version"] = geom.get("version", 1)

        # Also check for direct lat/lon fields
        if "lat" in item and "lon" in item:
            geometry["lat"] = float(item["lat"])
            geometry["lon"] = float(item["lon"])
            if "elevation" in item:
                geometry["elevation"] = int(item["elevation"])

        return geometry if geometry else None

    def _extract_locales(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract locale information from API response."""
        locales = {}

        # Check for locales field
        if "locales" in item:
            locales_data = item["locales"]
            if isinstance(locales_data, list):
                # Handle list format
                for locale_item in locales_data:
                    if isinstance(locale_item, dict) and "lang" in locale_item:
                        lang = locale_item["lang"]
                        locales[lang] = {
                            "title": locale_item.get("title"),
                            "title_prefix": locale_item.get("title_prefix"),
                            "description": locale_item.get("description"),
                            "summary": locale_item.get("summary"),
                            "access": locale_item.get("access"),
                            "access_period": locale_item.get("access_period"),
                            "remarks": locale_item.get("remarks"),
                            "gear": locale_item.get("gear"),
                            "external_resources": locale_item.get("external_resources"),
                            "route_history": locale_item.get("route_history"),
                            "approach": locale_item.get("approach"),
                            "descent": locale_item.get("descent"),
                            "conditions": locale_item.get("conditions"),
                            "weather": locale_item.get("weather"),
                            "snow_conditions": locale_item.get("snow_conditions"),
                            "rock_conditions": locale_item.get("rock_conditions"),
                            "ice_conditions": locale_item.get("ice_conditions"),
                            "mixed_conditions": locale_item.get("mixed_conditions"),
                            "avalanche_conditions": locale_item.get(
                                "avalanche_conditions"
                            ),
                            "glacier_conditions": locale_item.get("glacier_conditions"),
                            "river_conditions": locale_item.get("river_conditions"),
                            "sea_conditions": locale_item.get("sea_conditions"),
                            "other_conditions": locale_item.get("other_conditions"),
                            "slope": locale_item.get("slope"),
                            "slackline_anchor1": locale_item.get("slackline_anchor1"),
                            "slackline_anchor2": locale_item.get("slackline_anchor2"),
                            "version": locale_item.get("version"),
                            "lang": locale_item.get("lang"),
                        }
            elif isinstance(locales_data, dict):
                # Handle dict format
                for lang, lang_data in locales_data.items():
                    if isinstance(lang_data, dict):
                        locales[lang] = {
                            "title": lang_data.get("title"),
                            "title_prefix": lang_data.get("title_prefix"),
                            "description": lang_data.get("description"),
                            "summary": lang_data.get("summary"),
                            "access": lang_data.get("access"),
                            "access_period": lang_data.get("access_period"),
                            "remarks": lang_data.get("remarks"),
                            "gear": lang_data.get("gear"),
                            "external_resources": lang_data.get("external_resources"),
                            "route_history": lang_data.get("route_history"),
                            "approach": lang_data.get("approach"),
                            "descent": lang_data.get("descent"),
                            "conditions": lang_data.get("conditions"),
                            "weather": lang_data.get("weather"),
                            "snow_conditions": lang_data.get("snow_conditions"),
                            "rock_conditions": lang_data.get("rock_conditions"),
                            "ice_conditions": lang_data.get("ice_conditions"),
                            "mixed_conditions": lang_data.get("mixed_conditions"),
                            "avalanche_conditions": lang_data.get(
                                "avalanche_conditions"
                            ),
                            "glacier_conditions": lang_data.get("glacier_conditions"),
                            "river_conditions": lang_data.get("river_conditions"),
                            "sea_conditions": lang_data.get("sea_conditions"),
                            "other_conditions": lang_data.get("other_conditions"),
                            "slope": lang_data.get("slope"),
                            "slackline_anchor1": lang_data.get("slackline_anchor1"),
                            "slackline_anchor2": lang_data.get("slackline_anchor2"),
                            "version": lang_data.get("version"),
                            "lang": lang_data.get("lang"),
                        }

        return locales if locales else None

    def _extract_areas(self, item: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract area information from API response."""
        areas = []

        if "areas" in item and isinstance(item["areas"], list):
            for area in item["areas"]:
                if isinstance(area, dict):
                    area_data = {
                        "document_id": area.get("document_id"),
                        "version": area.get("version"),
                        "area_type": area.get("area_type"),
                        "available_langs": area.get("available_langs"),
                        "protected": area.get("protected"),
                        "type": area.get("type"),
                    }

                    # Extract area locales
                    if "locales" in area and isinstance(area["locales"], list):
                        area_locales = []
                        for locale in area["locales"]:
                            if isinstance(locale, dict):
                                locale_data = {
                                    "version": locale.get("version"),
                                    "lang": locale.get("lang"),
                                    "title": locale.get("title"),
                                }
                                area_locales.append(locale_data)
                        area_data["locales"] = area_locales

                    areas.append(area_data)

        return areas if areas else None

    async def get_routes(
        self,
        limit: int = 60_000,  # Set to 60k to cover all 55,660 routes
        offset: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        activities: Optional[List[str]] = None,
        difficulty_min: Optional[str] = None,
        difficulty_max: Optional[str] = None,
    ) -> List[Route]:
        """Fetch climbing routes from the API."""
        all_routes = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            if activities:
                params["act"] = ",".join(activities)
            if difficulty_min:
                params["diff_min"] = difficulty_min
            if difficulty_max:
                params["diff_max"] = difficulty_max

            response = await self._make_request("/routes", params)
            routes_batch = response.get("documents", [])

            if not routes_batch:
                break

            logger.info(
                f"Fetched {len(routes_batch)} routes (offset: {current_offset})"
            )

            for item in routes_batch:
                try:
                    # Extract and transform data
                    route_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Route"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "geometry": self._extract_geometry(item),
                        "difficulty": item.get("difficulty"),
                        "difficulty_rating": item.get("difficulty_rating"),
                        "exposure": item.get("exposure"),
                        "orientation": item.get("orientation"),
                        "height_diff_up": item.get("height_diff_up"),
                        "height_diff_down": item.get("height_diff_down"),
                        "length": item.get("length"),
                        "duration": item.get("duration"),
                        "seasons": item.get("seasons"),
                        "activities": item.get("activities"),
                        "climbing_outdoor_type": item.get("climbing_outdoor_type"),
                        "climbing_rating": item.get("climbing_rating"),
                        "climbing_rating_scale": item.get("climbing_rating_scale"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                        # Additional fields from database models
                        "elevation_min": item.get("elevation_min"),
                        "elevation_max": item.get("elevation_max"),
                        "durations": item.get("durations"),
                        "calculated_duration": item.get("calculated_duration"),
                        "height_diff_difficulties": item.get(
                            "height_diff_difficulties"
                        ),
                        "orientations": item.get("orientations"),
                        "global_rating": item.get("global_rating"),
                        "engagement_rating": item.get("engagement_rating"),
                        "risk_rating": item.get("risk_rating"),
                        "equipment_rating": item.get("equipment_rating"),
                        "exposition_rock_rating": item.get("exposition_rock_rating"),
                        "rock_free_rating": item.get("rock_free_rating"),
                        "rock_required_rating": item.get("rock_required_rating"),
                        "aid_rating": item.get("aid_rating"),
                        "public_transportation_rating": item.get(
                            "public_transportation_rating"
                        ),
                        "available_langs": item.get("available_langs"),
                        "areas": self._extract_areas(item),
                        # Additional route-specific fields from database
                        "difficulties_height": item.get("difficulties_height"),
                        "height_diff_access": item.get("height_diff_access"),
                        "route_types": item.get("route_types"),
                        "glacier_gear": item.get("glacier_gear"),
                        "configuration": item.get("configuration"),
                        "lift_access": item.get("lift_access"),
                        "ski_rating": item.get("ski_rating"),
                        "ski_exposition": item.get("ski_exposition"),
                        "labande_ski_rating": item.get("labande_ski_rating"),
                        "labande_global_rating": item.get("labande_global_rating"),
                        "via_ferrata_rating": item.get("via_ferrata_rating"),
                        "hiking_rating": item.get("hiking_rating"),
                        "hiking_mtb_exposition": item.get("hiking_mtb_exposition"),
                        "snowshoe_rating": item.get("snowshoe_rating"),
                        "mtb_up_rating": item.get("mtb_up_rating"),
                        "mtb_down_rating": item.get("mtb_down_rating"),
                        "mtb_length_asphalt": item.get("mtb_length_asphalt"),
                        "mtb_length_trail": item.get("mtb_length_trail"),
                        "mtb_height_diff_portages": item.get(
                            "mtb_height_diff_portages"
                        ),
                        "rock_types": item.get("rock_types"),
                        "slackline_type": item.get("slackline_type"),
                        "slackline_height": item.get("slackline_height"),
                        # Additional metadata fields
                        "document_id": item.get("document_id"),
                        "version": item.get("version"),
                        "status": item.get("status"),
                        "type": item.get("type"),
                        "protected": item.get("protected"),
                        "redirects_to": item.get("redirects_to"),
                        "redirects_to_document_id": item.get(
                            "redirects_to_document_id"
                        ),
                    }

                    # Filter out None values
                    route_data = {k: v for k, v in route_data.items() if v is not None}

                    route = Route(**route_data)
                    all_routes.append(route)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse route {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(routes_batch) >= total:
                logger.info(f"Reached total routes: {total}")
                break
            if len(all_routes) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(routes_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total routes collected: {len(all_routes)}")
        return all_routes

    async def get_waypoints(
        self,
        limit: int = 50000,  # Set to 50k to cover all 48,254 waypoints
        offset: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        waypoint_type: Optional[str] = None,
    ) -> List[Waypoint]:
        """Fetch waypoints from the API."""
        all_waypoints = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            if waypoint_type:
                params["wtyp"] = waypoint_type

            response = await self._make_request("/waypoints", params)
            waypoints_batch = response.get("documents", [])

            if not waypoints_batch:
                break

            logger.info(
                f"Fetched {len(waypoints_batch)} waypoints (offset: {current_offset})"
            )

            for item in waypoints_batch:
                try:
                    waypoint_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Waypoint"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "geometry": self._extract_geometry(item),
                        "waypoint_type": item.get("waypoint_type"),
                        "elevation": item.get("elevation"),
                        "activities": item.get("activities"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                        # Additional API fields from database models
                        "available_langs": item.get("available_langs"),
                        "areas": self._extract_areas(item),
                        # Additional waypoint-specific fields from database
                        "elevation_min": item.get("elevation_min"),
                        "height_max": item.get("height_max"),
                        "height_median": item.get("height_median"),
                        "height_min": item.get("height_min"),
                        "routes_quantity": item.get("routes_quantity"),
                        "climbing_outdoor_types": item.get("climbing_outdoor_types"),
                        "climbing_indoor_types": item.get("climbing_indoor_types"),
                        "climbing_rating_max": item.get("climbing_rating_max"),
                        "climbing_rating_min": item.get("climbing_rating_min"),
                        "climbing_rating_median": item.get("climbing_rating_median"),
                        "equipment_ratings": item.get("equipment_ratings"),
                        "climbing_styles": item.get("climbing_styles"),
                        "children_proof": item.get("children_proof"),
                        "rain_proof": item.get("rain_proof"),
                        "orientations": item.get("orientations"),
                        "best_periods": item.get("best_periods"),
                        "product_types": item.get("product_types"),
                        "length": item.get("length"),
                        "slope": item.get("slope"),
                        "ground_types": item.get("ground_types"),
                        "paragliding_rating": item.get("paragliding_rating"),
                        "exposition_rating": item.get("exposition_rating"),
                        "rock_types": item.get("rock_types"),
                        "weather_station_types": item.get("weather_station_types"),
                        "maps_info": item.get("maps_info"),
                        "public_transportation_types": item.get(
                            "public_transportation_types"
                        ),
                        "public_transportation_rating": item.get(
                            "public_transportation_rating"
                        ),
                        "snow_clearance_rating": item.get("snow_clearance_rating"),
                        "lift_access": item.get("lift_access"),
                        "parking_fee": item.get("parking_fee"),
                        "phone_custodian": item.get("phone_custodian"),
                        "custodianship": item.get("custodianship"),
                        "matress_unstaffed": item.get("matress_unstaffed"),
                        "blanket_unstaffed": item.get("blanket_unstaffed"),
                        "gas_unstaffed": item.get("gas_unstaffed"),
                        "heating_unstaffed": item.get("heating_unstaffed"),
                        "capacity_staffed": item.get("capacity_staffed"),
                        "slackline_types": item.get("slackline_types"),
                        "slackline_length_min": item.get("slackline_length_min"),
                        "slackline_length_max": item.get("slackline_length_max"),
                        # Additional metadata fields
                        "document_id": item.get("document_id"),
                        "version": item.get("version"),
                        "status": item.get("status"),
                        "type": item.get("type"),
                        "protected": item.get("protected"),
                        "redirects_to": item.get("redirects_to"),
                        "redirects_to_document_id": item.get(
                            "redirects_to_document_id"
                        ),
                    }

                    waypoint_data = {
                        k: v for k, v in waypoint_data.items() if v is not None
                    }
                    waypoint = Waypoint(**waypoint_data)
                    all_waypoints.append(waypoint)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse waypoint {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(waypoints_batch) >= total:
                logger.info(f"Reached total waypoints: {total}")
                break
            if len(all_waypoints) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(waypoints_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total waypoints collected: {len(all_waypoints)}")
        return all_waypoints

    async def get_articles(
        self,
        limit: int = 10000,  # Set to 10k to cover all articles
        offset: int = 0,
        article_type: Optional[str] = None,
    ) -> List[Article]:
        """Fetch collaborative articles from the API."""
        all_articles = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if article_type:
                params["atyp"] = article_type

            response = await self._make_request("/articles", params)
            articles_batch = response.get("documents", [])

            if not articles_batch:
                break

            logger.info(
                f"Fetched {len(articles_batch)} articles (offset: {current_offset})"
            )

            for item in articles_batch:
                try:
                    article_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Article"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "article_type": item.get("article_type"),
                        "activities": item.get("activities"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }

                    article_data = {
                        k: v for k, v in article_data.items() if v is not None
                    }
                    article = Article(**article_data)
                    all_articles.append(article)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse article {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(articles_batch) >= total:
                logger.info(f"Reached total articles: {total}")
                break
            if len(all_articles) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(articles_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles

    async def get_summits(
        self,
        limit: int = 10000,  # Set to 10k to cover all summits
        offset: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        elevation_min: Optional[int] = None,
        elevation_max: Optional[int] = None,
    ) -> List[Summit]:
        """Fetch mountain summits from the API."""
        all_summits = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            if elevation_min:
                params["elevation_min"] = elevation_min
            if elevation_max:
                params["elevation_max"] = elevation_max

            response = await self._make_request("/summits", params)
            summits_batch = response.get("documents", [])

            if not summits_batch:
                break

            logger.info(
                f"Fetched {len(summits_batch)} summits (offset: {current_offset})"
            )

            for item in summits_batch:
                try:
                    summit_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Summit"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "geometry": self._extract_geometry(item),
                        "elevation": item.get("elevation"),
                        "elevation_confidence": item.get("elevation_confidence"),
                        "prominence": item.get("prominence"),
                        "activities": item.get("activities"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }

                    summit_data = {
                        k: v for k, v in summit_data.items() if v is not None
                    }
                    summit = Summit(**summit_data)
                    all_summits.append(summit)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse summit {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(summits_batch) >= total:
                logger.info(f"Reached total summits: {total}")
                break
            if len(all_summits) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(summits_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total summits collected: {len(all_summits)}")
        return all_summits

    async def get_huts(
        self,
        limit: int = 10000,  # Set to 10k to cover all huts
        offset: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> List[Hut]:
        """Fetch mountain huts from the API."""
        all_huts = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

            response = await self._make_request("/huts", params)
            huts_batch = response.get("documents", [])

            if not huts_batch:
                break

            logger.info(f"Fetched {len(huts_batch)} huts (offset: {current_offset})")

            for item in huts_batch:
                try:
                    hut_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Hut"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "geometry": self._extract_geometry(item),
                        "elevation": item.get("elevation"),
                        "capacity": item.get("capacity"),
                        "phone": item.get("phone"),
                        "email": item.get("email"),
                        "website": item.get("website"),
                        "activities": item.get("activities"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }

                    hut_data = {k: v for k, v in hut_data.items() if v is not None}
                    hut = Hut(**hut_data)
                    all_huts.append(hut)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse hut {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(huts_batch) >= total:
                logger.info(f"Reached total huts: {total}")
                break
            if len(all_huts) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(huts_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total huts collected: {len(all_huts)}")
        return all_huts

    async def get_climbing_sites(
        self,
        limit: int = 10000,  # Set to 10k to cover all climbing sites
        offset: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> List[ClimbingSite]:
        """Fetch climbing sites from the API."""
        all_climbing_sites = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

            response = await self._make_request("/climbing_sites", params)
            climbing_sites_batch = response.get("documents", [])

            if not climbing_sites_batch:
                break

            logger.info(
                f"Fetched {len(climbing_sites_batch)} climbing sites (offset: {current_offset})"
            )

            for item in climbing_sites_batch:
                try:
                    climbing_site_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Climbing Site"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "geometry": self._extract_geometry(item),
                        "activities": item.get("activities"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }

                    climbing_site_data = {
                        k: v for k, v in climbing_site_data.items() if v is not None
                    }
                    climbing_site = ClimbingSite(**climbing_site_data)
                    all_climbing_sites.append(climbing_site)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse climbing site {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(climbing_sites_batch) >= total:
                logger.info(f"Reached total climbing sites: {total}")
                break
            if len(all_climbing_sites) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(climbing_sites_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total climbing sites collected: {len(all_climbing_sites)}")
        return all_climbing_sites

    async def get_outings(
        self,
        limit: int = 10000,  # Set to 10k to cover all outings
        offset: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> List[Outing]:
        """Fetch outings from the API."""
        all_outings = []
        current_offset = offset

        while True:
            params = {
                "limit": min(limit, 100),  # API max is 100 per request
                "offset": current_offset,
                "lang": "en,fr",
            }

            if bbox:
                params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

            response = await self._make_request("/outings", params)
            outings_batch = response.get("documents", [])

            if not outings_batch:
                break

            logger.info(
                f"Fetched {len(outings_batch)} outings (offset: {current_offset})"
            )

            for item in outings_batch:
                try:
                    outing_data = {
                        "id": item.get("document_id", item.get("id")),
                        "title": item.get("title", "Untitled Outing"),
                        "summary": item.get("summary"),
                        "locales": self._extract_locales(item),
                        "geometry": self._extract_geometry(item),
                        "elevation": item.get("elevation"),
                        "activities": item.get("activities"),
                        "url": item.get("url"),
                        "license": item.get("license"),
                        "quality": item.get("quality"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    }

                    outing_data = {
                        k: v for k, v in outing_data.items() if v is not None
                    }
                    outing = Outing(**outing_data)
                    all_outings.append(outing)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse outing {item.get('document_id', item.get('id', 'unknown'))}: {e}"
                    )

            # Check if we've reached the total or our limit
            total = response.get("total", 0)
            if total and current_offset + len(outings_batch) >= total:
                logger.info(f"Reached total outings: {total}")
                break
            if len(all_outings) >= limit:
                logger.info(f"Reached requested limit: {limit}")
                break

            current_offset += len(outings_batch)

            # Small delay to be respectful to the API
            await asyncio.sleep(0.1)

        logger.info(f"Total outings collected: {len(all_outings)}")
        return all_outings

    async def get_all_content(
        self,
        max_items_per_category: int = 60000,  # Set to 60k to cover all routes (55,660) and waypoints (48,254)
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> List[CamptocampItem]:
        """Fetch all content types from the API."""
        all_items = []

        # Define content types and their collection methods
        # Only include endpoints that are known to work
        content_types = [
            ("routes", self.get_routes),
            ("waypoints", self.get_waypoints),
            ("articles", self.get_articles),
            ("outings", self.get_outings),
        ]

        for content_type, collection_method in content_types:
            logger.info(f"Collecting {content_type}...")
            try:
                # Check if method supports bbox parameter
                import inspect

                sig = inspect.signature(collection_method)
                method_params = list(sig.parameters.keys())

                if "bbox" in method_params:
                    items = await collection_method(
                        limit=max_items_per_category, bbox=bbox
                    )
                else:
                    items = await collection_method(limit=max_items_per_category)

                # Convert to CamptocampItem format
                for item in items:
                    camptocamp_item = CamptocampItem(
                        item_type=content_type,
                        data=item,
                        raw_response=item.model_dump(),
                    )
                    all_items.append(camptocamp_item)

                logger.info(f"Collected {len(items)} {content_type}")

            except Exception as e:
                logger.error(f"Failed to collect {content_type}: {e}")
                logger.info(
                    f"Skipping {content_type} and continuing with other endpoints..."
                )

        return all_items

    def annotate_license_info(
        self, items: List[CamptocampItem]
    ) -> List[CamptocampItem]:
        """Annotate items with license information instead of filtering."""
        logger.info(f"Annotating license information for {len(items)} items...")

        license_counts = {}

        for item in items:
            # Get license from the parsed data
            license_value = getattr(item.data, "license", None)

            # Also check raw response for license info
            raw_license = (
                item.raw_response.get("license") if item.raw_response else None
            )

            # Use the most specific license information available
            final_license = license_value or raw_license

            # Count license types
            license_key = str(final_license) if final_license is not None else "null"
            license_counts[license_key] = license_counts.get(license_key, 0) + 1

            # Add license annotation to raw response for easy access
            if item.raw_response:
                item.raw_response["_annotated_license"] = final_license
                item.raw_response["_license_source"] = (
                    "parsed" if license_value else "raw"
                )

        # Log license distribution
        logger.info("License distribution:")
        for license_type, count in sorted(license_counts.items()):
            logger.info(f"  {license_type}: {count} items")

        return items

    def filter_cc_by_sa_content(
        self, items: List[CamptocampItem]
    ) -> List[CamptocampItem]:
        """Filter items to only include CC-BY-SA licensed content or content without explicit license restrictions."""
        logger.info(f"Filtering {len(items)} items for license compatibility...")
        filtered_items = []

        for item in items:
            # Accept items with CC-BY-SA license
            if hasattr(item.data, "license") and item.data.license == "CC-BY-SA":
                filtered_items.append(item)
                logger.debug(f"Item {item.data.id} has CC-BY-SA license")
            # Also check raw response for license info
            elif item.raw_response and item.raw_response.get("license") == "CC-BY-SA":
                filtered_items.append(item)
                logger.debug(
                    f"Item {item.data.id} has CC-BY-SA license in raw response"
                )
            # Accept items with null/None license (implicitly collaborative content)
            elif (hasattr(item.data, "license") and item.data.license is None) or (
                item.raw_response and item.raw_response.get("license") is None
            ):
                filtered_items.append(item)
                logger.debug(
                    f"Item {item.data.id} has no explicit license (implicitly collaborative)"
                )
            else:
                logger.debug(
                    f"Item {item.data.id} license: {getattr(item.data, 'license', 'None')} (raw: {item.raw_response.get('license') if item.raw_response else 'None'})"
                )

        logger.info(f"Filtered to {len(filtered_items)} license-compatible items")
        return filtered_items

    def filter_quality_content(
        self, items: List[CamptocampItem]
    ) -> List[CamptocampItem]:
        """Filter items to only include high-quality content."""
        quality_items = []

        for item in items:
            # Check if item has meaningful content
            has_content = False

            # Check parsed data first
            if hasattr(item.data, "locales"):
                locales = item.data.locales
                if locales:
                    for lang_content in [
                        locales.fr,
                        locales.en,
                        locales.de,
                        locales.it,
                        locales.es,
                    ]:
                        if lang_content:
                            # Check for various content fields that might be present
                            if any(
                                [
                                    getattr(lang_content, "description", None),
                                    getattr(lang_content, "summary", None),
                                    getattr(lang_content, "access", None),
                                    getattr(lang_content, "remarks", None),
                                    getattr(lang_content, "gear", None),
                                    getattr(lang_content, "route_history", None),
                                    getattr(lang_content, "approach", None),
                                    getattr(lang_content, "descent", None),
                                    getattr(lang_content, "conditions", None),
                                    getattr(lang_content, "weather", None),
                                ]
                            ):
                                has_content = True
                                break

            # Also check raw response for content
            if not has_content and item.raw_response:
                raw_locales = item.raw_response.get("locales", {})
                if isinstance(raw_locales, dict):
                    for lang, content in raw_locales.items():
                        if content and isinstance(content, dict):
                            # Check for various content fields in raw response
                            if any(
                                [
                                    content.get("description"),
                                    content.get("summary"),
                                    content.get("access"),
                                    content.get("remarks"),
                                    content.get("gear"),
                                    content.get("route_history"),
                                    content.get("approach"),
                                    content.get("descent"),
                                    content.get("conditions"),
                                    content.get("weather"),
                                ]
                            ):
                                has_content = True
                                break
                elif isinstance(raw_locales, list):
                    # Handle list format for locales
                    for locale_item in raw_locales:
                        if isinstance(locale_item, dict):
                            if any(
                                [
                                    locale_item.get("description"),
                                    locale_item.get("summary"),
                                    locale_item.get("access"),
                                    locale_item.get("remarks"),
                                    locale_item.get("gear"),
                                    locale_item.get("route_history"),
                                    locale_item.get("approach"),
                                    locale_item.get("descent"),
                                    locale_item.get("conditions"),
                                    locale_item.get("weather"),
                                ]
                            ):
                                has_content = True
                                break

            # For outings specifically, also check for outing-specific fields
            if not has_content and item.item_type == "outings":
                if item.raw_response:
                    # Check for outing-specific content fields
                    if any(
                        [
                            item.raw_response.get("conditions"),
                            item.raw_response.get("weather"),
                            item.raw_response.get("snow_conditions"),
                            item.raw_response.get("rock_conditions"),
                            item.raw_response.get("ice_conditions"),
                            item.raw_response.get("mixed_conditions"),
                            item.raw_response.get("avalanche_conditions"),
                            item.raw_response.get("glacier_conditions"),
                            item.raw_response.get("river_conditions"),
                            item.raw_response.get("sea_conditions"),
                            item.raw_response.get("other_conditions"),
                            item.raw_response.get("participants"),
                            item.raw_response.get("duration"),
                            item.raw_response.get("height_diff_up"),
                            item.raw_response.get("height_diff_down"),
                            item.raw_response.get("length"),
                            item.raw_response.get("difficulty"),
                            item.raw_response.get("exposure"),
                        ]
                    ):
                        has_content = True

            # For routes, also check for route-specific fields
            if not has_content and item.item_type == "routes":
                if item.raw_response:
                    # Check for route-specific content fields
                    if any(
                        [
                            item.raw_response.get("difficulty"),
                            item.raw_response.get("exposure"),
                            item.raw_response.get("orientation"),
                            item.raw_response.get("height_diff_up"),
                            item.raw_response.get("height_diff_down"),
                            item.raw_response.get("length"),
                            item.raw_response.get("duration"),
                            item.raw_response.get("seasons"),
                            item.raw_response.get("climbing_rating"),
                            item.raw_response.get("climbing_rating_scale"),
                        ]
                    ):
                        has_content = True

            # For waypoints, also check for waypoint-specific fields
            if not has_content and item.item_type == "waypoints":
                if item.raw_response:
                    # Check for waypoint-specific content fields
                    if any(
                        [
                            item.raw_response.get("waypoint_type"),
                            item.raw_response.get("elevation"),
                            item.raw_response.get("capacity"),
                            item.raw_response.get("phone"),
                            item.raw_response.get("email"),
                            item.raw_response.get("website"),
                        ]
                    ):
                        has_content = True

            if has_content:
                quality_items.append(item)

        return quality_items
