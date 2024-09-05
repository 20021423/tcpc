import os
import random


def generate_fully_satisfied_random_data(num_students):
    """
    Generates fully satisfied data for the Team Composition Problem in a Classroom (TCPC)
    but with randomized preferences for each student, ensuring fully satisfied groups.

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

    # Divide students into groups of 7
    for i in range(0, num_students, 7):
        group = students[i:i + 7]

        # Shuffle the group to randomize the preference order within the group
        random.shuffle(group)

        # 2 tables of 2 students and 1 table of 3 students for each group of 7
        tables = [
            group[0:2],  # First table with 2 students
            group[2:4],  # Second table with 2 students
            group[4:7],  # Third table with 3 students
        ]

        # Assign preferences for each student in a fully satisfied but random way
        for table in tables:
            for student in table:
                # Randomly select additional classmates outside of the table to fill up the preference list
                remaining_students = [s for s in students if s != student and s not in table]
                random.shuffle(remaining_students)
                preferences[student] = table.copy()  # Start with fully satisfied group
                preferences[student].remove(student)  # Remove the student themselves
                preferences[student] += remaining_students[
                                        :random.randint(0, len(remaining_students))]  # Add random classmates

    # Format the data as required
    formatted_data = f"{num_students}\n"
    for student in students:
        formatted_data += f"{student} " + " ".join(map(str, preferences[student])) + "\n"

    return formatted_data


def save_data_to_file(num_students, data, directory="data/fully"):
    """
    Save the generated fully satisfied random data to a file with a specific filename structure 'data_fully_random_X.txt'
    where X is the number of students.

    Args:
    - num_students (int): The number of students.
    - data (str): The generated formatted data.
    - directory (str): Directory where the file will be saved (default is 'data/fully_random').
    """
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Define the filename with the directory path
    filename = os.path.join(directory, f"students_preferences_{num_students}.txt")

    # Write the data to the file
    with open(filename, 'w') as f:
        f.write(data)
    print(f"Fully satisfied random data for {num_students} students saved to {filename}")


# Generate and save fully satisfied random data for multiples of 7 students (from 7 to 126)
for num_students in range(7, 127, 7):
    formatted_data = generate_fully_satisfied_random_data(num_students)
    save_data_to_file(num_students, formatted_data)
