import time

from ortools.sat.python import cp_model

def read_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    num_students = int(lines[0].strip())
    preferences = {}

    for line in lines[1:]:
        parts = list(map(int, line.strip().split()))
        student = parts[0] - 1
        preferences[student] = [p-1 for p in parts[1:]]

    return num_students, preferences

# Đường dẫn tới tệp dữ liệu
file_path = 'data/students_preferences_7.txt'

# Đọc dữ liệu từ tệp
num_students, preferences = read_data(file_path)

print(f"Số lượng học sinh: {num_students}")
print("Danh sách ưu tiên của học sinh:")
for student, prefs in preferences.items():
    print(f"Học sinh {student+1}: {prefs}")

# Tạo mô hình CP-SAT
model = cp_model.CpModel()

# Khởi tạo các biến
# x_ij là biến boolean đại diện cho việc học sinh i và j ngồi cùng bàn 2 người
x_ij = {}
for i in range(num_students):
    for j in range(i + 1, num_students):
        x_ij[(i, j)] = model.NewBoolVar(f'x_{i}_{j}')

# x_ijk là biến boolean đại diện cho việc học sinh i, j, và k ngồi cùng bàn 3 người
x_ijk = {}
for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            x_ijk[(i, j, k)] = model.NewBoolVar(f'x_{i}_{j}_{k}')


# y_i là biến boolean đại diện cho việc học sinh i ngồi bàn 2 người
y_i = {}
for i in range(num_students):
    y_i[i] = model.NewBoolVar(f'y_{i}')

# Ràng buộc: mỗi học sinh chỉ được ngồi một bàn (chia ra từng trường hợp cụ thể)
for i in range(num_students):
    if i == 0:
        clauses = [x_ij[i, j] for j in range(1, num_students)] + \
                  [x_ijk[i, j, k] for j in range(1, num_students - 1) for k in range(j + 1, num_students)]
    elif i == num_students - 1:
        clauses = [x_ij[j, i] for j in range(0, num_students - 1)] + \
                  [x_ijk[j, k, i] for j in range(0, num_students - 2) for k in range(j + 1, num_students - 1)]
    else:
        clauses = [x_ij[j, i] for j in range(0, i)] + \
                  [x_ij[i, j] for j in range(i + 1, num_students)] + \
                  [x_ijk[j, i, k] for j in range(0, i) for k in range(i + 1, num_students)] + \
                  [x_ijk[i, j, k] for j in range(i + 1, num_students - 1) for k in range(j + 1, num_students)]

    # Đảm bảo rằng mỗi học sinh chỉ được ngồi một bàn
    model.Add(sum(clauses) == 1)

# Ràng buộc ngồi bàn 2 người: nếu x_ij đúng thì y_i và y_j phải đúng
for i in range(num_students):
    for j in range(i + 1, num_students):
        if (i, j) in x_ij:
            model.Add(y_i[i] == 1).OnlyEnforceIf(x_ij[(i, j)])
            model.Add(y_i[j] == 1).OnlyEnforceIf(x_ij[(i, j)])

# Ràng buộc ngồi bàn 3 người: nếu x_ijk đúng thì y_i, y_j, y_k phải sai
for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            if (i, j, k) in x_ijk:
                model.Add(y_i[i] == 0).OnlyEnforceIf(x_ijk[(i, j, k)])
                model.Add(y_i[j] == 0).OnlyEnforceIf(x_ijk[(i, j, k)])
                model.Add(y_i[k] == 0).OnlyEnforceIf(x_ijk[(i, j, k)])

# Ràng buộc số lượng bàn cho 2 người
num_tables_2 = num_students // 7
num_tables_2 *= 4
print(num_tables_2, num_students)
model.Add(sum(y_i[i] for i in range(num_students)) == num_tables_2)


# Hàm mục tiêu: tối đa hóa sự hài lòng
objective = []

# Trọng số wij và wijk dựa trên sở thích của học sinh
for i in range(num_students):
    for j in range(i + 1, num_students):
        weight = 2 * (1 if j in preferences[i] else 0) * (1 if i in preferences[j] else 0)
        objective.append(weight * x_ij[(i, j)])

for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            weight = 3 * (len({j, k} & set(preferences[i])) * len({i, k} & set(preferences[j])) * len({i, j} & set(preferences[k])) / 8)
            objective.append(weight * x_ijk[(i, j, k)])

model.Maximize(sum(objective))

# Tính thời gian giải bài toán
start_time = time.time()
# Tạo solver và giải quyết bài toán
solver = cp_model.CpSolver()
status = solver.Solve(model)
solve_time = time.time() - start_time

# Hiển thị kết quả
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Solution:")
    for i in range(num_students):
        for j in range(i + 1, num_students):
            if solver.BooleanValue(x_ij[(i, j)]):
                print(f"Student {i + 1} sits with Student {j + 1}")
        for j in range(i + 1, num_students):
            for k in range(j + 1, num_students):
                if solver.BooleanValue(x_ijk[(i, j, k)]):
                    print(f"Student {i + 1} sits with Student {j + 1} and Student {k + 1}")
else:
    print("No solution found.")

print(solve_time)