"""
Core calculation logic for tile calculator
Adapted from sqcalc project
"""

import math
from typing import Dict, Tuple


# Tile size configurations
FLOOR_TILES = {
    "1x1": {"tiles_per_box": 10, "coverage_per_box": 10},  # 1x1 ft = 10 sq ft per box
    "2x2": {"tiles_per_box": 4, "coverage_per_box": 16},   # 2x2 ft = 16 sq ft per box
    "4x2": {"tiles_per_box": 2, "coverage_per_box": 16},   # 4x2 ft = 16 sq ft per box
}

WALL_TILES = {
    "12x8": {"tiles_per_box": 12, "coverage_per_box": 8},   # 12x8 inch = 8 sq ft per box
    "10x15": {"tiles_per_box": 8, "coverage_per_box": 9},   # 10x15 inch = 9 sq ft per box
    "12x18": {"tiles_per_box": 6, "coverage_per_box": 9},   # 12x18 inch = 9 sq ft per box
}


def round_up(value: float) -> int:
    """Round up to next integer (even 57.1 becomes 58)"""
    return math.ceil(value)


def calculate_custom_coverage(length: float, width: float, unit: str, tiles_per_box: int) -> float:
    """
    Calculate coverage per box for custom tile dimensions

    Args:
        length: Tile length
        width: Tile width
        unit: 'feet' or 'inch'
        tiles_per_box: Number of tiles per box

    Returns:
        Coverage per box in square feet
    """
    if unit == 'inch':
        # Convert inches to feet: (length * width) / 144
        tile_sq_ft = (length * width) / 144
    else:  # feet
        tile_sq_ft = length * width

    coverage = tile_sq_ft * tiles_per_box
    return round(coverage, 2)


class TileCalculator:
    """Calculate room dimensions and tile requirements"""

    def __init__(self):
        self.floor_tiles = FLOOR_TILES
        self.wall_tiles = WALL_TILES

    def calculate_floor_area(self, width: float, length: float) -> int:
        """
        Calculate floor area and round up to next integer

        Args:
            width: Room width in feet
            length: Room length in feet

        Returns:
            Area rounded up to next integer
        """
        if width <= 0 or length <= 0:
            raise ValueError("Width and length must be positive numbers")

        area = width * length
        return round_up(area)

    def calculate_wall_area(self, width: float, length: float, height: float,
                           deduct_door: bool = True) -> Tuple[int, int]:
        """
        Calculate wall area for tiling

        Args:
            width: Room width in feet
            length: Room length in feet
            height: Room height in feet
            deduct_door: Whether to deduct 2 feet for door entrance (default True)

        Returns:
            Tuple of (perimeter, wall_area) both rounded up
        """
        if width <= 0 or length <= 0 or height <= 0:
            raise ValueError("Width, length, and height must be positive numbers")

        # Calculate perimeter
        perimeter = 2 * (width + length)

        # Deduct 2 feet for door entrance
        if deduct_door:
            perimeter = perimeter - 2

        # Round up perimeter if decimal
        perimeter = round_up(perimeter)

        # Calculate wall area
        wall_area = perimeter * height

        # Round up area if decimal
        wall_area = round_up(wall_area)

        return perimeter, wall_area

    def calculate_floor_boxes_from_area(self, area: float,
                                       tile_size: str = None, tiles_per_box: int = None,
                                       coverage_per_box: float = None) -> Dict:
        """
        Calculate number of tile boxes needed for floor given direct area

        Args:
            area: Total floor area in square feet
            tile_size: Predefined tile size (e.g., "1x1", "2x2", "4x2") OR None for custom
            tiles_per_box: Number of tiles per box (for custom tiles)
            coverage_per_box: Coverage per box in sq ft (for custom tiles)

        Returns:
            Dictionary with calculation results
        """
        # Handle predefined tiles
        if tile_size and tile_size in self.floor_tiles:
            tile_config = self.floor_tiles[tile_size]
            coverage_per_box = tile_config["coverage_per_box"]
            tiles_per_box = tile_config["tiles_per_box"]
        # Handle custom tiles
        elif tiles_per_box and coverage_per_box:
            tile_size = "custom"
        else:
            raise ValueError("Either provide a valid tile_size or both tiles_per_box and coverage_per_box")

        # Round up area
        area = round_up(area)

        # Calculate boxes needed
        boxes_exact = area / coverage_per_box
        boxes_needed = round_up(boxes_exact)

        return {
            "category": "floor",
            "area": area,
            "tile_size": tile_size,
            "tiles_per_box": tiles_per_box,
            "coverage_per_box": coverage_per_box,
            "boxes_exact": round(boxes_exact, 2),
            "boxes_needed": boxes_needed
        }

    def calculate_floor_boxes(self, width: float, length: float,
                             tile_size: str = None, tiles_per_box: int = None,
                             coverage_per_box: float = None) -> Dict:
        """
        Calculate number of tile boxes needed for floor

        Args:
            width: Room width in feet
            length: Room length in feet
            tile_size: Predefined tile size (e.g., "1x1", "2x2", "4x2") OR None for custom
            tiles_per_box: Number of tiles per box (for custom tiles)
            coverage_per_box: Coverage per box in sq ft (for custom tiles)

        Returns:
            Dictionary with calculation results
        """
        # Handle predefined tiles
        if tile_size and tile_size in self.floor_tiles:
            tile_config = self.floor_tiles[tile_size]
            coverage_per_box = tile_config["coverage_per_box"]
            tiles_per_box = tile_config["tiles_per_box"]
        # Handle custom tiles
        elif tiles_per_box and coverage_per_box:
            tile_size = "custom"
        else:
            raise ValueError("Either provide a valid tile_size or both tiles_per_box and coverage_per_box")

        # Calculate area (rounded up)
        area = self.calculate_floor_area(width, length)

        # Calculate boxes needed
        boxes_exact = area / coverage_per_box
        boxes_needed = round_up(boxes_exact)

        return {
            "category": "floor",
            "width": width,
            "length": length,
            "area": area,
            "tile_size": tile_size,
            "tiles_per_box": tiles_per_box,
            "coverage_per_box": coverage_per_box,
            "boxes_exact": round(boxes_exact, 2),
            "boxes_needed": boxes_needed
        }

    def calculate_wall_boxes_from_area(self, wall_area: float,
                                      tile_size: str = None, deduct_door: bool = True,
                                      tiles_per_box: int = None, coverage_per_box: float = None) -> Dict:
        """
        Calculate number of tile boxes needed for walls given direct area

        Args:
            wall_area: Total wall area in square feet
            tile_size: Predefined tile size (e.g., "12x8", "10x15", "12x18") OR None for custom
            deduct_door: Whether door area was already deducted (for display purposes)
            tiles_per_box: Number of tiles per box (for custom tiles)
            coverage_per_box: Coverage per box in sq ft (for custom tiles)

        Returns:
            Dictionary with calculation results
        """
        # Handle predefined tiles
        if tile_size and tile_size in self.wall_tiles:
            tile_config = self.wall_tiles[tile_size]
            coverage_per_box = tile_config["coverage_per_box"]
            tiles_per_box = tile_config["tiles_per_box"]
        # Handle custom tiles
        elif tiles_per_box and coverage_per_box:
            tile_size = "custom"
        else:
            raise ValueError("Either provide a valid tile_size or both tiles_per_box and coverage_per_box")

        # Round up area
        wall_area = round_up(wall_area)

        # Calculate boxes needed
        boxes_exact = wall_area / coverage_per_box
        boxes_needed = round_up(boxes_exact)

        return {
            "category": "wall",
            "wall_area": wall_area,
            "door_deducted": deduct_door,
            "tile_size": tile_size,
            "tiles_per_box": tiles_per_box,
            "coverage_per_box": coverage_per_box,
            "boxes_exact": round(boxes_exact, 2),
            "boxes_needed": boxes_needed
        }

    def calculate_wall_boxes(self, width: float, length: float, height: float,
                            tile_size: str = None, deduct_door: bool = True,
                            tiles_per_box: int = None, coverage_per_box: float = None) -> Dict:
        """
        Calculate number of tile boxes needed for walls

        Args:
            width: Room width in feet
            length: Room length in feet
            height: Room height in feet
            tile_size: Predefined tile size (e.g., "12x8", "10x15", "12x18") OR None for custom
            deduct_door: Whether to deduct 2 feet for door entrance (default True)
            tiles_per_box: Number of tiles per box (for custom tiles)
            coverage_per_box: Coverage per box in sq ft (for custom tiles)

        Returns:
            Dictionary with calculation results
        """
        # Handle predefined tiles
        if tile_size and tile_size in self.wall_tiles:
            tile_config = self.wall_tiles[tile_size]
            coverage_per_box = tile_config["coverage_per_box"]
            tiles_per_box = tile_config["tiles_per_box"]
        # Handle custom tiles
        elif tiles_per_box and coverage_per_box:
            tile_size = "custom"
        else:
            raise ValueError("Either provide a valid tile_size or both tiles_per_box and coverage_per_box")

        # Calculate perimeter and wall area
        perimeter, wall_area = self.calculate_wall_area(width, length, height, deduct_door)

        # Calculate boxes needed
        boxes_exact = wall_area / coverage_per_box
        boxes_needed = round_up(boxes_exact)

        return {
            "category": "wall",
            "width": width,
            "length": length,
            "height": height,
            "perimeter": perimeter,
            "wall_area": wall_area,
            "door_deducted": deduct_door,
            "tile_size": tile_size,
            "tiles_per_box": tiles_per_box,
            "coverage_per_box": coverage_per_box,
            "boxes_exact": round(boxes_exact, 2),
            "boxes_needed": boxes_needed
        }
