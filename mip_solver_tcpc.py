from ortools.linear_solver import pywraplp
import time


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

# Tạo mô hình MIP
solver = pywraplp.Solver.CreateSolver('SCIP')

# Khởi tạo các biến
# x_ij là biến boolean đại diện cho việc học sinh i và j ngồi cùng bàn 2 người
x_ij = {}
for i in range(num_students):
    for j in range(i + 1, num_students):
        x_ij[(i, j)] = solver.BoolVar(f'x_{i}_{j}')

# x_ijk là biến boolean đại diện cho việc học sinh i, j, và k ngồi cùng bàn 3 người
x_ijk = {}
for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            x_ijk[(i, j, k)] = solver.BoolVar(f'x_{i}_{j}_{k}')

# y_i là biến boolean đại diện cho việc học sinh i ngồi bàn 2 người
y_i = {}
for i in range(num_students):
    y_i[i] = solver.BoolVar(f'y_{i}')

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
    solver.Add(sum(clauses) == 1)

# Ràng buộc ngồi bàn 2 người: nếu x_ij đúng thì y_i và y_j phải đúng
for i in range(num_students):
    for j in range(i + 1, num_students):
        if (i, j) in x_ij:
            solver.Add(y_i[i] >= x_ij[(i, j)])
            solver.Add(y_i[j] >= x_ij[(i, j)])

# Ràng buộc ngồi bàn 3 người: nếu x_ijk đúng thì y_i, y_j, y_k phải sai
for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            if (i, j, k) in x_ijk:
                solver.Add(y_i[i] <= 1 - x_ijk[(i, j, k)])
                solver.Add(y_i[j] <= 1 - x_ijk[(i, j, k)])
                solver.Add(y_i[k] <= 1 - x_ijk[(i, j, k)])

# Ràng buộc số lượng bàn cho 2 người
solver.Add(sum(y_i[i] for i in range(num_students)) == int(num_students * 4 / 7))

# Hàm mục tiêu: tối đa hóa sự hài lòng
# Trọng số wij và wijk dựa trên sở thích của học sinh
objective = solver.Objective()
for i in range(num_students):
    for j in range(i + 1, num_students):
        if (i, j) in x_ij:
            w_ij = 2 * (1 if j in preferences[i] else 0) * (1 if i in preferences[j] else 0)
            objective.SetCoefficient(x_ij[(i, j)], w_ij)
for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            if (i, j, k) in x_ijk:
                w_ijk = 3 * (len({j, k} & set(preferences[i])) * len({i, k} & set(preferences[j])) * len({i, j} & set(preferences[k])) / 8)
                objective.SetCoefficient(x_ijk[(i, j, k)], w_ijk)

objective.SetMaximization()

# Bắt đầu tính thời gian
start_time = time.time()

status = solver.Solve()

# Kết thúc tính thời gian
end_time = time.time()

# Tính thời gian giải quyết bài toán
solving_time = end_time - start_time

# Hiển thị kết quả
if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    print("Solution:")
    for i in range(num_students):
        for j in range(i + 1, num_students):
            if x_ij[(i, j)].solution_value() > 0.5:
                print(f"Student {i + 1} sits with Student {j + 1}")
        for j in range(i + 1, num_students):
            for k in range(j + 1, num_students):
                if x_ijk[(i, j, k)].solution_value() > 0.5:
                    print(f"Student {i + 1} sits with Student {j + 1} and Student {k + 1}")
else:
    print("No solution found.")

# In ra các thông số
print(f"Students: {num_students}")
print(f"Time_Max: {solving_time:.2f} seconds")
