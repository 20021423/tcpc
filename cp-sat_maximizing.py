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

# Đọc dữ liệu từ file
num_students, preferences = read_data('data/students_preferences_7.txt')
print(f"Số lượng học sinh: {num_students}")
print("Danh sách ưu tiên của học sinh:")
print(preferences)

# Tính toán trọng số
wij, wijk = calculate_weights(preferences, num_students)

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
    for j in range(i + 1, num_students + 1):
        for k in range(j + 1, num_students + 1):
            xijk_vars[(i, j, k)] = model.NewBoolVar(f'xijk_{i}_{j}_{k}')
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

# Objective: soft constraints for preferences
objective_terms = []
for (i, j), weight in wij.items():
    if weight > 0:
        objective_terms.append(xij_vars[(i, j)] * weight)

for (i, j, k), weight in wijk.items():
    if weight > 0:
        objective_terms.append(xijk_vars[(i, j, k)] * weight)

model.Maximize(sum(objective_terms))

# Solve the model
solver = cp_model.CpSolver()
start_time = time.time()
status = solver.Solve(model)
end_time = time.time()
elapsed_time = end_time - start_time

# Extract the solution
assigned_tables = {}
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for (i, j), var in xij_vars.items():
        if solver.Value(var):
            assigned_tables.setdefault(var, []).extend((i, j))
    for (i, j, k), var in xijk_vars.items():
        if solver.Value(var):
            assigned_tables.setdefault(var, []).extend((i, j, k))

# Loại bỏ các học sinh trùng lặp trong các nhóm
final_assigned_tables = [list(set(students)) for students in assigned_tables.values()]

# In kết quả
print("Assigned tables:", final_assigned_tables)

# Tổng kết
print(f"Students: {num_students}")
print(f"Time: {elapsed_time:.2f} seconds")
