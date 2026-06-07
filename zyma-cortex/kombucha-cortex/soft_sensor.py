import math
import time

def calculate_k_coefficient(t_liquid: float) -> float:
    """
    Calculates the temperature-dependent metabolic velocity coefficient (k)
    based on a piecewise-polynomial thermodynamic model.

    Args:
        t_liquid: The current liquid temperature in Celsius.

    Returns:
        The calculated k-coefficient.
    """
    if t_liquid < 22.0:
        # Phase of biomass anabiosis / dormancy
        return 0.00001
    elif 22.0 <= t_liquid < 27.0:
        # Normal operational profile
        return 0.00014 * (t_liquid / 24.0)
    elif 27.0 <= t_liquid <= 29.0:
        # Phase of metabolic intensification
        return 0.00022
    elif t_liquid > 29.0:
        # Thermal stress deceleration phase
        return 0.00005
    else:
        # Fallback for unexpected t_liquid values (e.g., 20.0 <= t_liquid < 22.0)
        # This branch ensures all ranges are covered. Given the specified ranges,
        # it logically falls into the dormancy phase or a transition.
        # For simplicity and adherence to piecewise, extending dormancy.
        return 0.00001


def predict_current_ph(ph_start: float, start_time_epoch: float, current_temp: float) -> float:
    """
    Predicts the current pH using a Luedeking-Piret kinetic first-principles
    pH virtual observer model, incorporating temperature-dependent metabolic velocity.

    Args:
        ph_start: The initial pH at the start of the fermentation.
        start_time_epoch: The Unix epoch timestamp (seconds) when fermentation started.
        current_temp: The current liquid temperature in Celsius.

    Returns:
        The predicted pH value, rounded to 3 decimal places.
    """
    # Calculate total elapsed minutes since the start of fermentation
    elapsed_minutes = (time.time() - start_time_epoch) / 60.0

    # Define the biological minimum saturation asymptote for pH
    ph_min = 2.5

    # Evaluate the exact mechanistic exponential model
    k_coefficient = calculate_k_coefficient(current_temp)
    predicted_ph = ph_min + (ph_start - ph_min) * math.exp(-k_coefficient * elapsed_minutes)

    return round(predicted_ph, 3)

