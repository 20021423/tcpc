from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from pysat.card import CardEnc, EncType
from itertools import combinations

# Bước 1: định nghĩa bài toán và đọc input
class TCPCInstance:
    def __init__(self, num_students, preferences):
        self.num_students = num_students  # Số lượng học sinh
        self.preferences = preferences  # Danh sách các sở thích

def read_data(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_students = int(lines[0].strip())
    preferences = {}
    for line in lines[1:]:
        parts = list(map(int, line.strip().split()))
        preferences[parts[0] - 1] = [p - 1 for p in parts[1:]]

    return TCPCInstance(num_students, preferences)

# Đọc dữ liệu từ file
instance = read_data('data/students_preferences_7.txt')
print(f"Số lượng học sinh: {instance.num_students}")
print("Danh sách ưu tiên của học sinh:")
for student, prefs in instance.preferences.items():
    print(f"Học sinh {student + 1}: {prefs}")

# Tạo đồ thị và tính trọng số
def build_graph(preferences):
    from collections import defaultdict

    graph = defaultdict(list)
    weights = defaultdict(int)

    for student, prefs in preferences.items():
        for pref in prefs:
            graph[student].append(pref)
            weights[student] += 1

    return graph, weights

# Tạo đồ thị và tính trọng số
graph, weights = build_graph(instance.preferences)

# Bước 3: Mô hình hóa bài toán bằng các biến Boolean và thêm các ràng buộc cứng và mềm
class TCPCModel:
    def __init__(self, instance, graph, weights):
        self.instance = instance
        self.graph = graph
        self.weights = weights
        self.wcnf = WCNF()
        self.var_map = {}
        self.inverse_var_map = {}
        self.current_var = 1

    def get_var(self, name):
        if name not in self.var_map:
            self.var_map[name] = self.current_var
            self.inverse_var_map[self.current_var] = name
            self.current_var += 1
        return self.var_map[name]

    def add_hard_constraint(self, clause):
        self.wcnf.append(clause)

    def add_soft_constraint(self, clause, weight):
        self.wcnf.append(clause, weight=weight)

    def build_model(self):
        students = list(range(self.instance.num_students))
        num_students = self.instance.num_students
        num_tables_2 = (num_students // 7) * 4

        # Ràng buộc 1: Mỗi học sinh chỉ ngồi đúng 1 bàn
        for i in range(num_students):
            if i == 0:
                clauses = [self.get_var(f"x_{i}_{j}") for j in range(1, num_students)] + \
                          [self.get_var(f"x_{i}_{j}_{k}") for j in range(1, num_students - 1) for k in
                           range(j + 1, num_students)]
            elif i == num_students - 1:
                clauses = [self.get_var(f"x_{j}_{i}") for j in range(0, num_students - 1)] + \
                          [self.get_var(f"x_{j}_{k}_{i}") for j in range(0, num_students - 2) for k in
                           range(j + 1, num_students - 1)]
            else:
                clauses = [self.get_var(f"x_{j}_{i}") for j in range(0, i)] + \
                          [self.get_var(f"x_{i}_{j}") for j in range(i + 1, num_students)] + \
                          [self.get_var(f"x_{j}_{i}_{k}") for j in range(0, i) for k in range(i + 1, num_students)] + \
                          [self.get_var(f"x_{i}_{j}_{k}") for j in range(i + 1, num_students - 1) for k in
                           range(j + 1, num_students)]
            for m in range(len(clauses)):
                        for n in range(m + 1, len(clauses)):
                            self.wcnf.append([-clauses[m], -clauses[n]])

        # Ràng buộc 2: Nếu xij đúng thì yi và yj cũng phải đúng
        for table in combinations(students, 2):
            i, j = table
            var_x = self.get_var(f"x_{i}_{j}")
            var_yi = self.get_var(f"y_{i}")
            var_yj = self.get_var(f"y_{j}")
            self.add_hard_constraint([-var_x, var_yi])
            self.add_hard_constraint([-var_x, var_yj])

        # Ràng buộc 3: Nếu xijk đúng thì yi, yj, yk phải sai
        for table in combinations(students, 3):
            i, j, k = table
            var_x = self.get_var(f"x_{i}_{j}_{k}")
            var_yi = self.get_var(f"y_{i}")
            var_yj = self.get_var(f"y_{j}")
            var_yk = self.get_var(f"y_{k}")
            self.add_hard_constraint([-var_x, -var_yi])
            self.add_hard_constraint([-var_x, -var_yj])
            self.add_hard_constraint([-var_x, -var_yk])

        # Ràng buộc 4: Tổng số học sinh ngồi bàn 2 người bằng đúng số bàn 2 người
        y_vars = [self.get_var(f"y_{i}") for i in students]
        card_constraint = CardEnc.equals(lits=y_vars, bound=num_tables_2, encoding=EncType.seqcounter)
        for clause in card_constraint.clauses:
            self.wcnf.append(clause)

        # Các ràng buộc mềm dựa trên sở thích và trọng số
        for table in combinations(students, 2):
            i, j = table
            var = self.get_var(f"x_{i}_{j}")
            wi = 1 if j in self.graph[i] else 0
            wj = 1 if i in self.graph[j] else 0
            wij = 2 * (wi * wj)
            if wij > 0:
                self.add_soft_constraint([var], wij)

        for table in combinations(students, 3):
            i, j, k = table
            var = self.get_var(f"x_{i}_{j}_{k}")
            wi = sum([1 if x in self.graph[i] else 0 for x in [j, k]])
            wj = sum([1 if x in self.graph[j] else 0 for x in [i, k]])
            wk = sum([1 if x in self.graph[k] else 0 for x in [i, j]])
            wijk = 3 * (wi * wj * wk) / 8
            if wijk > 0:
                self.add_soft_constraint([var], wijk)
print("Graph:", graph)
# Khởi tạo và xây dựng mô hình
model = TCPCModel(instance, graph, weights)
model.build_model()
print(model)
# Bước 4: Sử dụng MaxSAT Solver
# Giải quyết bài toán
solver = RC2(model.wcnf)
print(1)
solution = solver.compute()
print(2)
# In ra kết quả
for var in solution:
    if var > 0:
        print(f"Variable {model.inverse_var_map[var]} is True")
