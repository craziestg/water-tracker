#!/usr/bin/env python3
"""
Simple unit tests for water_tracker conversion functions.

Tests the to_ml() and ml_to_oz() conversion helpers to ensure
correct unit conversions between ml, liters, and ounces.

Run with: pytest test_water_tracker.py
Or:       python -m pytest test_water_tracker.py
"""

from water_tracker import to_ml, ml_to_oz, WaterTrackerApp


class TestConversions:
    """Test suite for unit conversion functions."""

    # ---- Tests for to_ml() ----

    def test_to_ml_from_ml():
        """Test converting milliliters to milliliters (identity)."""
        assert to_ml("250", "ml") == 250
        assert to_ml("1000", "ml") == 1000

    def test_to_ml_from_ml_case_insensitive():
        """Test that unit string is case-insensitive."""
        assert to_ml("250", "ML") == 250
        assert to_ml("250", "Ml") == 250

    def test_to_ml_from_liters():
        """Test converting liters to milliliters (1L = 1000ml)."""
        assert to_ml("1", "L") == 1000
        assert to_ml("1.5", "L") == 1500
        assert to_ml("0.5", "L") == 500

    def test_to_ml_from_liters_verbose():
        """Test conversion with full unit names."""
        assert to_ml("2", "liter") == 2000
        assert to_ml("2", "liters") == 2000

    def test_to_ml_from_ounces():
        """Test converting ounces to milliliters (1 oz ≈ 29.57 ml).
        
        Expected: 355 ml is roughly 12 oz (standard can size in USA).
        """
        # 12 oz should be approximately 355 ml
        result = to_ml("12", "oz")
        assert abs(result - 355) <= 1, f"Expected ~355, got {result}"

    def test_to_ml_from_ounces_single():
        """Test a single ounce conversion."""
        # 1 oz ≈ 29.57 ml
        result = to_ml("1", "oz")
        assert abs(result - 30) <= 1, f"Expected ~30, got {result}"

    def test_to_ml_invalid_unit():
        """Test that invalid units raise ValueError."""
        try:
            to_ml("250", "gallons")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "unsupported unit" in str(e).lower()

    def test_to_ml_float_input():
        """Test that float inputs are properly converted."""
        assert to_ml("1.5", "ml") == 2  # rounds 1.5 to 2
        assert to_ml("1.4", "ml") == 1  # rounds 1.4 to 1

    # ---- Tests for ml_to_oz() ----

    def test_ml_to_oz_standard_can():
        """Test converting 355 ml (standard US can) to ounces.
        
        355 ml should be approximately 12 oz.
        """
        result = ml_to_oz(355)
        assert abs(result - 12) < 0.5, f"Expected ~12 oz, got {result}"

    def test_ml_to_oz_liter():
        """Test converting 1000 ml (1 liter) to ounces (~33.8 oz)."""
        result = ml_to_oz(1000)
        assert abs(result - 33.8) < 0.5, f"Expected ~33.8 oz, got {result}"

    def test_ml_to_oz_returns_float():
        """Test that ml_to_oz() returns a float."""
        result = ml_to_oz(250)
        assert isinstance(result, float)


# Standalone test functions for manual testing
def test_to_ml_from_ml():
    """Test converting milliliters to milliliters (identity)."""
    assert to_ml("250", "ml") == 250
    assert to_ml("1000", "ml") == 1000

def test_to_ml_from_liters():
    """Test converting liters to milliliters (1L = 1000ml)."""
    assert to_ml("1", "L") == 1000
    assert to_ml("1.5", "L") == 1500
    assert to_ml("0.5", "L") == 500

def test_to_ml_from_ounces():
    """Test converting ounces to milliliters (1 oz ≈ 29.57 ml).
    
    Expected: 355 ml is roughly 12 oz (standard can size in USA).
    """
    # 12 oz should be approximately 355 ml
    result = to_ml("12", "oz")
    assert abs(result - 355) <= 1, f"Expected ~355, got {result}"

def test_ml_to_oz_standard_can():
    """Test converting 355 ml (standard US can) to ounces.
    
    355 ml should be approximately 12 oz.
    """
    result = ml_to_oz(355)
    assert abs(result - 12) < 0.5, f"Expected ~12 oz, got {result}"


# ---- Tests for progress bar colors ----
def test_progress_bar_red_color():
    """Test that progress bar shows red color when < 75% complete."""
    import tkinter as tk
    from datetime import datetime
    
    # Create a minimal Tkinter root for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create app instance
        app = WaterTrackerApp()
        
        # Set goal to 2000 ml
        app.settings["daily_goal_ml"] = 2000
        
        # Simulate 500 ml logged (25% complete - should be red)
        # Use today's date for the timestamp so it gets counted
        today_str = datetime.now().isoformat()
        app.log = [{"timestamp": today_str, "amount_ml": 500}]
        app.update_stats()
        app.update()  # Ensure canvas has been drawn and scheduled updates run

        # Check that progress bar color is red
        current_color = app.progress_canvas.itemcget(app._progress_bar_item, 'fill')
        assert current_color == '#FF6B6B', f"Expected red color '#FF6B6B', got '{current_color}'"
        
        print("✓ Progress bar red color test passed")
        
    finally:
        root.destroy()


def test_progress_bar_yellow_color():
    """Test that progress bar shows yellow color when 75%+ complete."""
    import tkinter as tk
    from datetime import datetime
    
    # Create a minimal Tkinter root for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create app instance
        app = WaterTrackerApp()
        
        # Set goal to 2000 ml
        app.settings["daily_goal_ml"] = 2000
        
        # Simulate 1600 ml logged (80% complete - should be yellow)
        # Use today's date for the timestamp so it gets counted
        today_str = datetime.now().isoformat()
        app.log = [{"timestamp": today_str, "amount_ml": 1600}]
        app.update_stats()
        app.update()  # Ensure canvas has been drawn and scheduled updates run

        # Check that progress bar color is yellow
        current_color = app.progress_canvas.itemcget(app._progress_bar_item, 'fill')
        assert current_color == '#FFD93D', f"Expected yellow color '#FFD93D', got '{current_color}'"
        
        print("✓ Progress bar yellow color test passed")
        
    finally:
        root.destroy()


def test_progress_bar_green_color():
    """Test that progress bar shows green color when 100%+ complete."""
    import tkinter as tk
    from datetime import datetime
    
    # Create a minimal Tkinter root for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create app instance
        app = WaterTrackerApp()
        
        # Set goal to 2000 ml
        app.settings["daily_goal_ml"] = 2000
        
        # Simulate 2100 ml logged (105% complete - should be green)
        # Use today's date for the timestamp so it gets counted
        today_str = datetime.now().isoformat()
        app.log = [{"timestamp": today_str, "amount_ml": 2100}]
        app.update_stats()
        app.update()  # Ensure canvas has been drawn and scheduled updates run

        # Check that progress bar color is green
        current_color = app.progress_canvas.itemcget(app._progress_bar_item, 'fill')
        assert current_color == '#6BCF7F', f"Expected green color '#6BCF7F', got '{current_color}'"
        
        print("✓ Progress bar green color test passed")
        
    finally:
        root.destroy()


# ---- Tests for goal estimates ----
def test_goal_estimates_calculation():
    """Test that goal estimates calculate correctly."""
    import tkinter as tk
    from datetime import datetime

    # Create a minimal Tkinter root for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window

    try:
        # Create app instance
        app = WaterTrackerApp()

        # Set goal to 2000 ml
        app.settings["daily_goal_ml"] = 2000

        # Simulate 500 ml logged (1500 ml remaining)
        today_str = datetime.now().isoformat()
        app.log = [{"timestamp": today_str, "amount_ml": 500}]
        app.update_stats()
        app._update_goal_estimates()  # Directly call estimates update

        # Check that estimates text contains expected calculations
        estimates_content = app.estimates_text.get(1.0, tk.END).strip()
        assert "Need 1500 ml more:" in estimates_content
        assert "4.2 × Can 355 ml" in estimates_content
        assert "1.3 × Bottle 1180 ml" in estimates_content
        assert "6.2 × Cup 240 ml" in estimates_content

        print("✓ Goal estimates calculation test passed")

    finally:
        root.destroy()


if __name__ == "__main__":
    # Quick manual test if not using pytest
    print("Running manual tests...")
    try:
        test_to_ml_from_ml()
        print("✓ test_to_ml_from_ml")
        test_to_ml_from_liters()
        print("✓ test_to_ml_from_liters")
        test_to_ml_from_ounces()
        print("✓ test_to_ml_from_ounces")
        test_ml_to_oz_standard_can()
        print("✓ test_ml_to_oz_standard_can")
        
        # Test progress bar colors
        test_progress_bar_red_color()
        test_progress_bar_yellow_color()
        test_progress_bar_green_color()
        
        # Test goal estimates
        test_goal_estimates_calculation()
        
        print("\nAll manual tests passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
