# backend/kernel/models/vocabulary.py

"""
Canonical, well-known vocabulary for the kernel.

IMPORTANT DESIGN DECISION
-------------------------
Entity roles and spatial relation kinds are stored as plain `str` on the
models (open set), NOT as closed `Literal` types.

Why?
- The kernel must stay generic and plugin-friendly.
- Plugins may introduce NEW roles / relations without modifying the kernel.
- We still provide a rich, canonical set of known values here so that
  core plugins share a consistent vocabulary and get good ergonomics.

So: the field type is open (`str`), but these constants define the
"blessed" / canonical values the kernel and first-party plugins use.
"""

from __future__ import annotations

from enum import StrEnum


class EntityRole(StrEnum):
    """Canonical entity roles. Open set: plugins may use custom strings too."""

    # --- primary search roles ---
    TARGET = "target"                     # what the user is looking for
    ANCHOR = "anchor"                     # reference point of the search
    SECONDARY_TARGET = "secondary_target" # second target (comparisons)

    # --- routing roles ---
    ORIGIN = "origin"
    DESTINATION = "destination"
    WAYPOINT = "waypoint"
    VIA = "via"

    # --- area roles ---
    AREA = "area"
    BOUNDARY = "boundary"
    REGION = "region"

    # --- constraint roles ---
    CONSTRAINT = "constraint"
    FILTER = "filter"
    EXCLUSION = "exclusion"

    # --- supportive roles ---
    CONTEXT = "context"
    MODIFIER = "modifier"
    ATTRIBUTE = "attribute"
    QUANTITY = "quantity"
    TIME = "time"
    UNIT = "unit"

    # --- fallback ---
    UNKNOWN = "unknown"


class RelationKind(StrEnum):
    """Canonical spatial relation kinds. Open set: plugins may extend."""

    # --- proximity ---
    NEARBY = "nearby"
    NEAREST = "nearest"
    WITHIN = "within"
    WITHIN_WALKING = "within_walking"
    WITHIN_DRIVING = "within_driving"

    # --- topology ---
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"
    INTERSECTS = "intersects"
    OVERLAPS = "overlaps"
    TOUCHES = "touches"
    DISJOINT = "disjoint"

    # --- direction / position ---
    NORTH_OF = "north_of"
    SOUTH_OF = "south_of"
    EAST_OF = "east_of"
    WEST_OF = "west_of"
    ADJACENT = "adjacent"
    BETWEEN = "between"
    ALONG = "along"

    # --- routing ---
    ROUTE = "route"
    SHORTEST_PATH = "shortest_path"
    FASTEST_PATH = "fastest_path"
    REACHABLE = "reachable"

    # --- comparison / aggregation ---
    COMPARE = "compare"
    COUNT = "count"
    AGGREGATE = "aggregate"
    DENSITY = "density"

    # --- simple lookup ---
    LOCATE = "locate"
    SEARCH = "search"

    # --- fallback ---
    UNKNOWN = "unknown"


class GeometryHint(StrEnum):
    """Canonical, provider-agnostic geometry hints. Open set."""

    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"
    MULTIPOINT = "multipoint"
    MULTILINE = "multiline"
    MULTIPOLYGON = "multipolygon"
    GEOMETRY_COLLECTION = "geometry_collection"
    UNKNOWN = "unknown"


class QueryIntent(StrEnum):
    """
    Canonical high-level query intents.

    Defined here early so QueryIR (Phase 2.3) can reuse it. Open set.
    """

    LOCATE = "locate"          # where is X
    NEARBY = "nearby"          # X around Y
    NEAREST = "nearest"        # nearest X to Y
    WITHIN = "within"          # X within radius/area of Y
    ROUTE = "route"            # route from A to B
    COMPARE = "compare"        # compare X and Y
    COUNT = "count"            # how many X
    AGGREGATE = "aggregate"    # aggregate stats
    FILTER = "filter"          # filtered search
    SEARCH = "search"          # generic search
    UNKNOWN = "unknown"
