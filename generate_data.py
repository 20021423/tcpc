import random


def generate_simulated_data(num_students):
    """
    Generates simulated data for the Team Composition Problem in a Classroom (TCPC) with the desired format.

    Args:
    - num_students (int): Total number of students (multiple of 7).

    Returns:
    - formatted_data (str): Formatted data with students and their preferences.
    """
    if num_students % 7 != 0:
        raise ValueError("Number of students must be a multiple of 7.")

    # Initialize the list of students
    students = list(range(1, num_students + 1))

    # Initialize preferences as an empty dictionary
    preferences = {}

    # Generate preferences for each student
    for student in students:
        # Randomly select a subset of other students (size from 1 to num_students-1, ensuring no preference for oneself)
        preferred_classmates = random.sample([s for s in students if s != student], random.randint(1, num_students - 1))
        preferences[student] = preferred_classmates

    # Format the data as required
    formatted_data = f"{num_students}\n"
    for student in students:
        formatted_data += f"{student} " + " ".join(map(str, preferences[student])) + "\n"

    return formatted_data


def save_data_to_file(num_students, data):
    """
    Save the generated data to a file with a specific filename structure 'students_preferences_X.txt' where X is the number of students.

    Args:
    - num_students (int): The number of students.
    - data (str): The generated formatted data.
    """
    filename = f"students_preferences_{num_students}.txt"
    with open(filename, 'w') as f:
        f.write(data)
    print(f"Data for {num_students} students saved to {filename}")


# Generate and save data for multiples of 7 students (from 7 to 126)
for num_students in range(7, 127, 7):
    formatted_data = generate_simulated_data(num_students)
    save_data_to_file(num_students, formatted_data)
