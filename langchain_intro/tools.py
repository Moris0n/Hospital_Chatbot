import random
import time

def get_current_wait_time(hospital_name: str) -> int | str:
    """Dummy function to generate fake wait times"""

    if hospital_name not in ["A", "B", "C", "D"]:
        return f"Hospital {hospital_name} does not exist"

    # Simulate API call delay
    time.sleep(1)

    return random.randint(0, 10000)
