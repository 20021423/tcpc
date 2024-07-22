import time
from ortools.sat.python import cp_model

def read_data(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_students = int(lines[0].strip())
    preferences = {}
    for line in lines[1:]:
        parts = list(map(int, line.strip().split()))
        preferences[parts[0]] = parts[1:]

    return num_students, preferences


# Read data from file
num_students, preferences = read_data('data/students_preferences_35.txt')
print(f"Số lượng học sinh: {num_students}")
print("Danh sách ưu tiên của học sinh:")
print(preferences)

# Create a CP-SAT model
model = cp_model.CpModel()

# Define Boolean variables
xij_vars = {}
xijk_vars = {}
y_vars = {}

# Initialize variables
for i in range(1, num_students + 1):
    for j in range(i + 1, num_students + 1):
        xij_vars[(i, j)] = model.NewBoolVar(f'xij_{i}_{j}')
for i in range(1, num_students + 1):
    for j in range(i + 1, num_students + 1):
        for k in range(j + 1, num_students + 1):
            xijk_vars[(i, j, k)] = model.NewBoolVar(f'xijk_{i}_{j}_{k}')
for i in range(1, num_students + 1):
    y_vars[i] = model.NewBoolVar(f'y_{i}')

# Hard clauses for single assignment
for i in range(1, num_students + 1):
    clause = []
    if i == 1:
        clause = [xij_vars[(i, j)] for j in range(2, num_students + 1)]
        clause += [xijk_vars[(i, j, k)] for j in range(2, num_students) for k in range(j + 1, num_students + 1)]
    elif 2 <= i <= num_students - 1:
        clause = [xij_vars[(j, i)] for j in range(1, i)] + [xij_vars[(i, j)] for j in range(i + 1, num_students + 1)]
        clause += [xijk_vars[(j, k, i)] for k in range(2, i) for j in range(1, k)] + [xijk_vars[(j, i, k)] for j in range(1, i) for k in range(i + 1, num_students + 1)] + [xijk_vars[(i, j, k)] for j in range(i + 1, num_students) for k in range(j + 1, num_students + 1)]
    else:  # i == num_students
        clause = [xij_vars[(j, i)] for j in range(1, num_students)]
        clause += [xijk_vars[(j, k, i)] for j in range(1, num_students - 1) for k in range(j + 1, num_students)]

    model.Add(sum(clause) == 1)

# Hard clauses for valid table assignments
for (i, j) in xij_vars:
    model.AddImplication(xij_vars[(i, j)], y_vars[i])
    model.AddImplication(xij_vars[(i, j)], y_vars[j])

for (i, j, k) in xijk_vars:
    model.AddImplication(xijk_vars[(i, j, k)], y_vars[i].Not())
    model.AddImplication(xijk_vars[(i, j, k)], y_vars[j].Not())
    model.AddImplication(xijk_vars[(i, j, k)], y_vars[k].Not())

# Cardinality constraint
num_tables_2 = int(num_students * 4 / 7)
model.Add(sum(y_vars.values()) == num_tables_2)

def calculate_weights(preferences, num_students):
    out_degrees = {i: 0 for i in range(1, num_students + 1)}
    for i, friends in preferences.items():
        out_degrees[i] = len(friends)

    wij = {}
    wijk = {}

    for i in range(1, num_students + 1):
        for j in range(i + 1, num_students + 1):
            subgraph_out_degrees = {
                v: sum(1 for neighbor in preferences.get(v, []) if neighbor in {i, j})
                for v in [i, j]
            }
            wi = subgraph_out_degrees[i]
            wj = subgraph_out_degrees[j]
            wij[(i, j)] = 2 * wi * wj
        for j in range(i + 1, num_students + 1):
            for k in range(j + 1, num_students + 1):
                subgraph_out_degrees = {
                    v: sum(1 for neighbor in preferences.get(v, []) if neighbor in {i, j, k})
                    for v in [i, j, k]
                }
                wi = subgraph_out_degrees[i]
                wj = subgraph_out_degrees[j]
                wk = subgraph_out_degrees[k]
                wijk[(i, j, k)] = 3 * wi * wj * wk / 8
    return wij, wijk

# Tính toán trọng số
wij, wijk = calculate_weights(preferences, num_students)

wmax = 2
wmax_prime = 3

# Objective: soft constraints for preferences (Minimizing Encoding)
# Trọng số wij và wijk dựa trên sở thích của học sinh
model.Minimize(
    sum(
        (wmax - 2 * (1 if j in preferences[i] else 0) * (1 if i in preferences[j] else 0)) * xij_vars[(i, j)]
        for i in range(1, num_students + 1)
        for j in range(i + 1, num_students + 1)
        if (i, j) in xij_vars
    ) +
    sum(
        (wmax_prime - 3 * (len({j, k} & set(preferences[i])) * len({i, k} & set(preferences[j])) * len({i, j} & set(preferences[k])) / 8)) * xijk_vars[(i, j, k)]
        for i in range(1, num_students + 1)
        for j in range(i + 1, num_students + 1)
        for k in range(j + 1, num_students + 1)
        if (i, j, k) in xijk_vars
    )
)


# Solve the model
solver = cp_model.CpSolver()
start_time = time.time()
status = solver.Solve(model)
end_time = time.time()
elapsed_time = end_time - start_time

# Extract the solution
assigned_tables = []
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for (i, j), var in xij_vars.items():
        if solver.Value(var):
            assigned_tables.append(sorted([i, j]))
    for (i, j, k), var in xijk_vars.items():
        if solver.Value(var):
            assigned_tables.append(sorted([i, j, k]))

# Sort the assigned tables
assigned_tables.sort()

# Print the results
print("Assigned tables:")
for table in assigned_tables:
    print(table)

# Summary
print(f"Students: {num_students}")
print(f"Time: {elapsed_time:.2f} seconds")

# Calculate the total weight of the assigned tables
def calculate_assigned_weight(assigned_tables, wij, wijk):
    total_weight = 0
    for table in assigned_tables:
        if len(table) == 2:
            i, j = table
            if (i, j) in wij:
                total_weight += wij[(i, j)]
        elif len(table) == 3:
            i, j, k = table
            if (i, j, k) in wijk:
                total_weight += wijk[(i, j, k)]
    return total_weight

total_weight = calculate_assigned_weight(assigned_tables, wij, wijk)
print(f"Total weight: {total_weight}")