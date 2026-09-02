# patient_utils.py
# This file contains utility functions for working with patient data.
# Each function handles one specific task, which makes the code
# easy to read, test, and reuse across different parts of the application.


# Import the config file to use the shared application settings
import config




def format_patient_name(first_name: str, last_name: str) -> str:
    """
    Formats a patient's first name and last name into a single display string.
    
    The output format is: Last Name, First Name
    This is the standard format used in medical records.
    
    Parameters:
        first_name (str): The patient's first name
        last_name (str): The patient's last name
    
    Returns:
        str: The formatted name string
    """
    # Strip extra spaces from both names before combining them
    first_name = first_name.strip()
    last_name = last_name.strip()
    
    # Return the name in Last, First format
    return f"{last_name}, {first_name}"




def is_valid_patient_id(patient_id: str) -> bool:
    """
    Checks whether a patient ID follows the required format.
    
    A valid patient ID must:
        - Start with the letters PT followed by a hyphen
        - Be followed by exactly 6 digits
        - Example: PT-000123
    
    Parameters:
        patient_id (str): The patient ID string to validate
    
    Returns:
        bool: True if the ID is valid, False otherwise
    """
    # Import the regular expression module for pattern matching
    import re
    
    # Define the required pattern: PT- followed by exactly 6 digits
    pattern = r"^PT-\d{6}$"
    
    # Check if the patient_id matches the pattern
    # re.match returns a match object if found, or None if not found
    return bool(re.match(pattern, patient_id))




def get_role_display_name(role_code: str) -> str:
    """
    Converts an internal role code into a human-readable display name.
    
    Uses the role constants defined in config.py to ensure consistency.
    If an unknown role code is passed, a safe default is returned.
    
    Parameters:
        role_code (str): One of the role constants from config.py
    
    Returns:
        str: A readable label for the role
    """
    # Map each internal role code to a display-friendly string
    role_map = {
        config.ROLE_PATIENT: "Patient",
        config.ROLE_DOCTOR: "Doctor",
        config.ROLE_BILLING: "Billing Staff",
    }
    
    # Return the matching display name, or 'Unknown Role' as a safe default
    return role_map.get(role_code, "Unknown Role")

