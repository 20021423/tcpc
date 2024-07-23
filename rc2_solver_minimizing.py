import time
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from pysat.card import CardEnc, EncType

def read_data(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_students = int(lines[0].strip())
    preferences = {}
    for line in lines[1:]:
        parts = list(map(int, line.strip().split()))
        preferences[parts[0]] = parts[1:]

    return num_students, preferences


num_students, preferences = read_data('data/students_preferences_21.txt')
print(f"Số lượng học sinh: {num_students}")
print("Danh sách ưu tiên của học sinh:")
print(preferences)

# Create a WCNF formula
formula = WCNF()

# Define Boolean variables
xij_vars = {}
xijk_vars = {}
y_vars = {}

# Initialize variables
var_index = 1
for i in range(1, num_students + 1):
    for j in range(i + 1, num_students + 1):
        xij_vars[(i, j)] = var_index
        var_index += 1
    for j in range(i + 1, num_students + 1):
        for k in range(j + 1, num_students + 1):
            xijk_vars[(i, j, k)] = var_index
            var_index += 1
    y_vars[i] = var_index
    var_index += 1

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

    formula.append(clause)
    for m in range(len(clause)):
        for n in range(m + 1, len(clause)):
            formula.append([-clause[m], -clause[n]])

# Hard clauses for valid table assignments
for (i, j) in xij_vars:
    formula.append([-xij_vars[(i, j)], y_vars[i]])
    formula.append([-xij_vars[(i, j)], y_vars[j]])

for (i, j, k) in xijk_vars:
    formula.append([-xijk_vars[(i, j, k)], -y_vars[i]])
    formula.append([-xijk_vars[(i, j, k)], -y_vars[j]])
    formula.append([-xijk_vars[(i, j, k)], -y_vars[k]])

# Cardinality constraint
num_tables_2 = int(num_students * 4 / 7)
card_constraint = CardEnc.equals(lits=list(y_vars.values()), bound=num_tables_2, encoding=EncType.seqcounter)
for clause in card_constraint.clauses:
    formula.append(clause)

def calculate_weights_minimizing(preferences, num_students):
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
wij, wijk = calculate_weights_minimizing(preferences, num_students)

# Objective: soft constraints for preferences (Minimizing Encoding)
for (i, j), weight in wij.items():
    if weight < 2 :
        formula.append([-xij_vars[(i, j)]], weight=2 - weight)

for (i, j, k), weight in wijk.items():
    if weight < 3:
        formula.append([-xijk_vars[(i, j, k)]], weight=3 - weight)



# Solve the model
solver = RC2(formula)
start_time = time.time()

try:
    solution = solver.compute()
except MemoryError:
    print("Memory Error: Problem too large to fit in RAM.")
    solution = None

end_time = time.time()
elapsed_time = end_time - start_time

# Extract the solution
assigned_tables = {}
if solution:
    for var in solution:
        if var > 0:
            if var in xij_vars.values():
                for key, value in xij_vars.items():
                    if value == var:
                        assigned_tables.setdefault(var, []).extend(key)
            elif var in xijk_vars.values():
                for key, value in xijk_vars.items():
                    if value == var:
                        assigned_tables.setdefault(var, []).extend(key)

# Remove duplicates in groups
final_assigned_tables = [list(set(students)) for students in assigned_tables.values()]

# Print the results
print("Assigned tables:", final_assigned_tables)

# Summary
print(f"Students: {num_students}")
print(f"Time: {elapsed_time:.2f} seconds")


def calculate_satisfied_weights(solution, xij_vars, xijk_vars, wij, wijk):
    satisfied_wij = 0
    satisfied_wijk = 0

    for var in solution:
        if var > 0:
            for (i, j), v in xij_vars.items():
                if v == var:
                    satisfied_wij += wij.get((i, j), 0)
            for (i, j, k), v in xijk_vars.items():
                if v == var:
                    satisfied_wijk += wijk.get((i, j, k), 0)

    return satisfied_wij + satisfied_wijk

print("total weights: ", calculate_satisfied_weights(solution, xij_vars, xijk_vars, wij, wijk))

