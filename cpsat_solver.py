import time
from ortools.sat.python import cp_model

class TeamCompositionCPSATSolver:
    def __init__(self, num_students, preferences, encoding_type='max'):
        self.num_students = num_students
        self.preferences = preferences
        self.encoding_type = encoding_type  # 'max' or 'min'
        self.model = cp_model.CpModel()
        self.xij_vars = {}
        self.xijk_vars = {}
        self.y_vars = {}
        self.hard_count = 0
        self.soft_count = 0
        self.variable_count = 0  # Đếm tổng số biến
        self.total_weight = 0  # Lưu tổng trọng số
        self.solve_time = 0  # Lưu thời gian chạy
        self.assigned_tables = []  # Lưu danh sách các bàn đã sắp xếp
        self._initialize_variables()

    def _initialize_variables(self):
        """ Khởi tạo các biến Boolean cho mô hình. """
        for i in range(1, self.num_students + 1):
            for j in range(i + 1, self.num_students + 1):
                self.xij_vars[(i, j)] = self.model.NewBoolVar(f'xij_{i}_{j}')
                self.variable_count += 1  # Tăng biến đếm số lượng biến
            for j in range(i + 1, self.num_students + 1):
                for k in range(j + 1, self.num_students + 1):
                    self.xijk_vars[(i, j, k)] = self.model.NewBoolVar(f'xijk_{i}_{j}_{k}')
                    self.variable_count += 1  # Tăng biến đếm số lượng biến
            self.y_vars[i] = self.model.NewBoolVar(f'y_{i}')
            self.variable_count += 1  # Tăng biến đếm số lượng biến

    def add_hard_clauses(self):
        """ Thêm các ràng buộc cứng vào mô hình. """
        self._add_single_assignment_clauses()
        self._add_valid_table_clauses()
        self._add_cardinality_constraint()

    def _add_single_assignment_clauses(self):
        """ Thêm ràng buộc đảm bảo mỗi sinh viên được phân vào đúng một bàn. """
        for i in range(1, self.num_students + 1):
            clause = self._get_single_assignment_clause(i)
            self.model.Add(sum(clause) == 1)
            self.hard_count += 1

    def _get_single_assignment_clause(self, i):
        """ Tạo mệnh đề cho việc phân bàn của sinh viên i. """
        clause = []
        if i == 1:
            clause = [self.xij_vars[(i, j)] for j in range(2, self.num_students + 1)]
            clause += [self.xijk_vars[(i, j, k)] for j in range(2, self.num_students) for k in range(j + 1, self.num_students + 1)]
        elif 2 <= i <= self.num_students - 1:
            clause = [self.xij_vars[(j, i)] for j in range(1, i)] + [self.xij_vars[(i, j)] for j in range(i + 1, self.num_students + 1)]
            clause += [self.xijk_vars[(j, k, i)] for k in range(2, i) for j in range(1, k)]
            clause += [self.xijk_vars[(j, i, k)] for j in range(1, i) for k in range(i + 1, self.num_students + 1)]
            clause += [self.xijk_vars[(i, j, k)] for j in range(i + 1, self.num_students) for k in range(j + 1, self.num_students + 1)]
        else:  # i == num_students
            clause = [self.xij_vars[(j, i)] for j in range(1, self.num_students)]
            clause += [self.xijk_vars[(j, k, i)] for j in range(1, self.num_students - 1) for k in range(j + 1, self.num_students)]
        return clause

    def _add_valid_table_clauses(self):
        """ Thêm ràng buộc đảm bảo các phân bàn hợp lệ. """
        for (i, j) in self.xij_vars:
            self.model.AddImplication(self.xij_vars[(i, j)], self.y_vars[i])
            self.model.AddImplication(self.xij_vars[(i, j)], self.y_vars[j])
            self.hard_count += 2

        for (i, j, k) in self.xijk_vars:
            self.model.AddImplication(self.xijk_vars[(i, j, k)], self.y_vars[i].Not())
            self.model.AddImplication(self.xijk_vars[(i, j, k)], self.y_vars[j].Not())
            self.model.AddImplication(self.xijk_vars[(i, j, k)], self.y_vars[k].Not())
            self.hard_count += 3

    def _add_cardinality_constraint(self):
        """ Thêm ràng buộc cho số lượng bàn. """
        num_tables_2 = int(self.num_students * 4 / 7)
        self.model.Add(sum(self.y_vars.values()) == num_tables_2)
        self.hard_count += 1

    def calculate_weights(self):
        """ Tính toán trọng số dựa trên sở thích của sinh viên. """
        out_degrees = {i: 0 for i in range(1, self.num_students + 1)}
        for i, friends in self.preferences.items():
            out_degrees[i] = len(friends)

        wij = {}
        wijk = {}

        for i in range(1, self.num_students + 1):
            for j in range(i + 1, self.num_students + 1):
                subgraph_out_degrees = {
                    v: sum(1 for neighbor in self.preferences.get(v, []) if neighbor in {i, j})
                    for v in [i, j]
                }
                wi = subgraph_out_degrees[i]
                wj = subgraph_out_degrees[j]
                wij[(i, j)] = 2 * wi * wj
            for j in range(i + 1, self.num_students + 1):
                for k in range(j + 1, self.num_students + 1):
                    subgraph_out_degrees = {
                        v: sum(1 for neighbor in self.preferences.get(v, []) if neighbor in {i, j, k})
                        for v in [i, j, k]
                    }
                    wi = subgraph_out_degrees[i]
                    wj = subgraph_out_degrees[j]
                    wk = subgraph_out_degrees[k]
                    wijk[(i, j, k)] = 3 * wi * wj * wk / 8
        return wij, wijk

    def add_soft_clauses(self, wij, wijk):
        """ Thêm ràng buộc mềm vào mô hình dựa trên loại mã hóa đã chọn. """
        if self.encoding_type == 'min':
            self._add_soft_clauses_minimizing(wij, wijk)
        elif self.encoding_type == 'max':
            self._add_soft_clauses_maximizing(wij, wijk)
        else:
            raise ValueError("Invalid encoding type. Use 'min' for minimizing or 'max' for maximizing.")

    def _add_soft_clauses_minimizing(self, wij, wijk):
        """ Thêm ràng buộc mềm cho việc tối thiểu hóa. """
        objective_terms = []

        for (i, j), weight in wij.items():
            if weight < 2:
                # Mục tiêu là giảm thiểu số lượng biến được chọn có trọng số thấp
                objective_terms.append((2 - weight) * self.xij_vars[(i, j)])
                self.soft_count += 1

        for (i, j, k), weight in wijk.items():
            if weight < 3:
                # Mục tiêu là giảm thiểu số lượng biến được chọn có trọng số thấp
                objective_terms.append((3 - weight) * self.xijk_vars[(i, j, k)])
                self.soft_count += 1

        # Thêm vào hàm mục tiêu để tối thiểu hóa tổng các điều khoản
        self.model.Minimize(sum(objective_terms))

    def _add_soft_clauses_maximizing(self, wij, wijk):
        """ Thêm ràng buộc mềm cho việc tối đa hóa. """
        objective_terms = []
        for (i, j), weight in wij.items():
            if weight > 0:
                objective_terms.append(self.xij_vars[(i, j)] * weight)
                self.soft_count += 1

        for (i, j, k), weight in wijk.items():
            if weight > 0:
                objective_terms.append(self.xijk_vars[(i, j, k)] * weight)
                self.soft_count += 1

        self.model.Maximize(sum(objective_terms))

    def solve(self):
        """ Giải quyết mô hình bằng bộ giải CP-SAT và lưu thời gian chạy. """
        self.add_hard_clauses()
        wij, wijk = self.calculate_weights()
        self.add_soft_clauses(wij, wijk)

        solver = cp_model.CpSolver()
        start_time = time.time()
        status = solver.Solve(self.model)
        self.solve_time = time.time() - start_time

        # Lấy tổng trọng số được tối ưu hóa từ solver
        self.total_weight = solver.ObjectiveValue()
        if(self.encoding_type == 'min'):
            self.total_weight = self.num_students - self.total_weight

        # self.assigned_tables = []
        # if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        #     for (i, j), var in self.xij_vars.items():
        #         if solver.Value(var):
        #             self.assigned_tables.append(sorted([i, j]))
        #     for (i, j, k), var in self.xijk_vars.items():
        #         if solver.Value(var):
        #             self.assigned_tables.append(sorted([i, j, k]))
        #
        # self.total_weight = self.extract_solution_and_calculate_weights(self.assigned_tables)

    def extract_solution_and_calculate_weights(self, assigned_tables):
        """ Tính toán tổng trọng số được thỏa mãn dựa trên các bàn đã phân. """
        wij, wijk = self.calculate_weights()
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

    def get_stats(self):
        """ Trả về các thống kê như số biến, số mệnh đề, trọng số và thời gian giải. """
        return {
            'hard_clauses': self.hard_count,
            'soft_clauses': self.soft_count,
            'variables': self.variable_count,
            'total_weight': self.total_weight,
            'solve_time': self.solve_time,
        }

    def print_assigned_tables(self):
        """ In ra danh sách các bàn đã được sắp xếp """
        print("Assigned tables:")
        for table in self.assigned_tables:
            print(table)


def read_data(filename):
    """ Đọc sở thích của sinh viên từ file. """
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_students = int(lines[0].strip())
    preferences = {}
    for line in lines[1:]:
        parts = list(map(int, line.strip().split()))
        preferences[parts[0]] = parts[1:]

    return num_students, preferences


if __name__ == "__main__":
    input_data = 'data/max/max_70.txt'
    num_students, preferences = read_data(input_data)

    solver = TeamCompositionCPSATSolver(num_students, preferences, encoding_type='min')
    solver.solve()
    stats = solver.get_stats()

    # In các thống kê ra
    print(f"Number of variables: {stats['variables']}")
    print(f"Number of hard clauses: {stats['hard_clauses']}")
    print(f"Number of soft clauses: {stats['soft_clauses']}")
    print(f"Total satisfied weight: {stats['total_weight']}")
    print(f"Solve time: {stats['solve_time']:} seconds")

    # # In danh sách các bàn đã sắp xếp
    # solver.print_assigned_tables()
