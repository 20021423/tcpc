import time

from pysat.card import CardEnc, EncType
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

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

# Khởi tạo đối tượng WCNF
cnf = WCNF()

# Biến số đại diện cho việc hai học sinh ngồi cùng bàn
# x_ij là biến đại diện cho việc học sinh i và j ngồi cùng bàn cho 2 người
x_ij = {}
count = 1
for i in range(num_students):
    for j in range(i + 1, num_students):
        x_ij[(i, j)] = count
        count += 1
# x_ijk là biến đại diện cho việc học sinh i, j và k ngồi cùng bàn cho 3 người
x_ijk = {}
for i in range(num_students):
    for j in range(i + 1, num_students):
        for k in range(j + 1, num_students):
            x_ijk[(i, j, k)] = count
            count += 1

# y_i là biến đại diện cho việc học sinh i ngồi ở bàn cho 2 người
y_i = {}
for i in range(num_students):
    y_i[i] = count
    count += 1

# Cardinality constraints encoding: Mỗi học sinh chỉ ngồi một bàn
for i in range(num_students):
    if i == 0:
        clauses = [x_ij[(i, j)] for j in range(1, num_students)] + \
                  [x_ijk[(i, j, k)] for j in range(1, num_students - 1) for k in range(j + 1, num_students)]
    elif i == num_students - 1:
        clauses = [x_ij[(j, i)] for j in range(0, num_students - 1)] +\
                  [x_ijk[(j, k, i)] for j in range(0, num_students - 2) for k in range(j + 1, num_students - 1)]
    else:
        clauses = [x_ij[(j, i)] for j in range(0, i)] + \
                  [x_ij[(i, j)] for j in range(i + 1, num_students)] + \
                  [x_ijk[(j, i, k)] for j in range(0, i) for k in range(i + 1, num_students)] + \
                  [x_ijk[(i, j, k)] for j in range(i + 1, num_students - 1) for k in range(j + 1, num_students)]

    cnf.append(clauses)
    for m in range(len(clauses)):
        for n in range(m + 1, len(clauses)):
            cnf.append([-clauses[m], -clauses[n]])

# Ràng buộc cho bàn 2 và 3 người
for i in range(num_students):
    # Các ràng buộc đảm bảo mỗi bàn có đúng số học sinh
    for j in range(i + 1, num_students):
        cnf.append([-x_ij[(i, j)], y_i[i]])  # Nếu x_ij là đúng thì i và j phải ngồi ở bàn cho 2 người
        cnf.append([-x_ij[(i, j)], y_i[j]])
        for k in range(j + 1, num_students):
            cnf.append([-x_ijk[(i, j, k)], -y_i[i]])  # Nếu x_ijk là đúng thì i, j và k phải ngồi ở bàn cho 3 người
            cnf.append([-x_ijk[(i, j, k)], -y_i[j]])
            cnf.append([-x_ijk[(i, j, k)], -y_i[k]])

# Đảm bảo đúng số lượng bàn cho 2 người và 3 người
y_vars = [y_i[i] for i in range(num_students)]
num_tables_2 = num_students // 7
num_tables_2 *= 4
print(num_tables_2, num_students)
card_constraint = CardEnc.equals(lits=y_vars, bound=num_tables_2, encoding=EncType.seqcounter)
for clause in card_constraint.clauses:
    cnf.append(clause)

# Thêm ràng buộc mềm với trọng số
# Tính trọng số wij
for i in range(num_students):
    for j in range(i + 1, num_students):
        w_i = 1 if j in preferences[i] else 0
        w_j = 1 if i in preferences[j] else 0
        w = 2 * (w_i * w_j)
        if w == 0:
            cnf.append([-x_ij[(i, j)]])
        if w > 0:
            cnf.append([x_ij[(i, j)]], w)

# Tính trọng số wijk
for i in range(num_students):
    for j in range(i + 1, num_students - 1):
        for k in range(j + 1, num_students):
            w_i = len({j, k} & set(preferences[i]))
            w_j = len({i, k} & set(preferences[j]))
            w_k = len({i, j} & set(preferences[k]))
            w = 3 * ((w_i * w_j * w_k) / 8)
            if w ==0 :
                cnf.append([-x_ijk[(i, j, k)]])
            if w > 0:
                cnf.append([x_ijk[(i, j, k)]], w)

# Sử dụng RC2 để giải bài toán MaxSAT
solver = RC2(cnf)
start = time.time()
solution = solver.compute()
end = time.time()
if solution != None:
    print("Tìm thấy giải pháp tối ưu.")
    # In ra các cặp học sinh ngồi cùng nhau từ giải pháp
    print("Các cặp học sinh ngồi cùng nhau:")
    for i in range(num_students):
        for j in range(i + 1, num_students):
            if solution[x_ij[(i, j)] - 1] > 0:
                print(f"Học sinh {i + 1} và học sinh {j + 1} ngồi cùng nhau.")

        for j in range(i + 1, num_students):
            for k in range(j + 1, num_students):
                if solution[x_ijk[(i, j, k)] - 1] > 0:
                    print(f"Học sinh {i + 1}, học sinh {j + 1} và học sinh {k + 1} ngồi cùng nhau.")
else:
    print("Không tìm thấy giải pháp tối ưu.")
print(end-start)