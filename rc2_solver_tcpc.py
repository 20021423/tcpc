import os
import time
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF, IDPool
from pysat.card import CardEnc, EncType

class TeamCompositionSolver:
    def __init__(self, num_students, preferences, encoding_type='min'):
        self.num_students = num_students
        self.preferences = preferences
        self.encoding_type = encoding_type  # 'min' or 'max'
        self.formula = WCNF()
        self.vpool = IDPool(start_from=1)  # ID Pool for managing variables
        self.xij_vars = {}
        self.xijk_vars = {}
        self.y_vars = {}
        self.total_weight = 0  # Lưu tổng trọng số
        self.solve_time = 0  # Lưu thời gian chạy
        self.assigned_tables = []  # Lưu danh sách các bàn đã sắp xếp
        self.hard_count = 0
        self.soft_count = 0
        self._initialize_variables()

    def _initialize_variables(self):
        """ Initialize Boolean variables for the formula. """
        for i in range(1, self.num_students + 1):
            for j in range(i + 1, self.num_students + 1):
                self.xij_vars[(i, j)] = self.vpool.id()
            for j in range(i + 1, self.num_students + 1):
                for k in range(j + 1, self.num_students + 1):
                    self.xijk_vars[(i, j, k)] = self.vpool.id()
            self.y_vars[i] = self.vpool.id()

    def add_hard_clauses(self):
        """ Add hard constraints to the formula. """
        self._add_single_assignment_clauses()
        self._add_valid_table_clauses()
        self._add_cardinality_constraint()

    def _add_single_assignment_clauses(self):
        """ Add constraints ensuring each student is assigned to exactly one table. """
        for i in range(1, self.num_students + 1):
            clause = self._get_single_assignment_clause(i)
            card_enc_atmost = CardEnc.atmost(lits=clause, bound=1, vpool=self.vpool, encoding=EncType.seqcounter)
            for c in card_enc_atmost.clauses:
                self.formula.append(c)
            self.formula.append(clause)

    def _get_single_assignment_clause(self, i):
        """ Generate clause for single assignment of student i. """
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
        self.hard_count += 1
        return clause

    def _add_valid_table_clauses(self):
        """ Add constraints ensuring valid table assignments. """
        for (i, j) in self.xij_vars:
            self.formula.append([-self.xij_vars[(i, j)], self.y_vars[i]])
            self.formula.append([-self.xij_vars[(i, j)], self.y_vars[j]])
            self.hard_count += 2
        for (i, j, k) in self.xijk_vars:
            self.formula.append([-self.xijk_vars[(i, j, k)], -self.y_vars[i]])
            self.formula.append([-self.xijk_vars[(i, j, k)], -self.y_vars[j]])
            self.formula.append([-self.xijk_vars[(i, j, k)], -self.y_vars[k]])
            self.hard_count += 3

    def _add_cardinality_constraint(self):
        """ Add cardinality constraints for the number of tables. """
        num_tables_2 = int(self.num_students * 4 / 7)
        card_constraint = CardEnc.equals(lits=list(self.y_vars.values()), bound=num_tables_2, vpool=self.vpool, encoding=EncType.seqcounter)
        for clause in card_constraint.clauses:
            self.formula.append(clause)
        self.hard_count += 1

    def calculate_weights(self):
        """ Calculate weights based on the chosen encoding type. """
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
        """ Add soft constraints to the formula based on encoding type. """
        if self.encoding_type == 'min':
            self._add_soft_clauses_minimizing(wij, wijk)
        elif self.encoding_type == 'max':
            self._add_soft_clauses_maximizing(wij, wijk)
        else:
            raise ValueError("Invalid encoding type. Use 'min' for minimizing or 'max' for maximizing.")

    def _add_soft_clauses_minimizing(self, wij, wijk):
        """ Add soft constraints for minimizing encoding. """
        for (i, j), weight in wij.items():
            if weight < 2:
                self.formula.append([-self.xij_vars[(i, j)]], weight=2 - weight)
                self.soft_count += 1

        for (i, j, k), weight in wijk.items():
            if weight < 3:
                self.formula.append([-self.xijk_vars[(i, j, k)]], weight=3 - weight)
                self.soft_count += 1

    def _add_soft_clauses_maximizing(self, wij, wijk):
        """ Add soft constraints for maximizing encoding. """
        for (i, j), weight in wij.items():
            if weight == 2:
                self.formula.append([self.xij_vars[(i, j)]], weight=int(weight))
                self.soft_count += 1

        for (i, j, k), weight in wijk.items():
            if weight == 3:
                self.formula.append([self.xijk_vars[(i, j, k)]], weight=int(weight))
                self.soft_count += 1

    def solve(self):
        """ Giải bài toán MaxSAT và đo thời gian """
        self.add_hard_clauses()
        # Tính toán trước các trọng số wij, wijk và lưu lại
        self.wij, self.wijk = self.calculate_weights()
        self.add_soft_clauses(self.wij, self.wijk)

        solver = RC2(self.formula)
        start_time = time.time()
        solution = solver.compute()
        self.solve_time = time.time() - start_time
        self.total_weight = sum(self.formula.wght) - solver.cost
        if self.encoding_type == 'min':
            self.total_weight = self.num_students - solver.cost

        # # # Giải mã kết quả và tính toán tổng trọng số
        # # self.assigned_tables, self.total_weight = self.extract_solution_and_calculate_weights(solution)


    def extract_solution_and_calculate_weights(self, solution):
        """ Giải mã và tính tổng trọng số được thỏa mãn """
        assigned_tables = {}
        total_satisfied_weight = 0

        if solution:
            # Duyệt qua tất cả các biến dương (các biến được gán giá trị true trong solution)
            for var in solution:
                if var > 0:
                    # Nếu biến dương thuộc xij_vars
                    for (i, j), v in self.xij_vars.items():
                        if v == var:
                            assigned_tables.setdefault(var, []).extend([i, j])
                            total_satisfied_weight += self.wij.get((i, j), 0)
                            break  # Khi tìm thấy biến khớp, không cần tiếp tục duyệt
                    # Nếu biến dương thuộc xijk_vars
                    for (i, j, k), v in self.xijk_vars.items():
                        if v == var:
                            assigned_tables.setdefault(var, []).extend([i, j, k])
                            total_satisfied_weight += self.wijk.get((i, j, k), 0)
                            break  # Khi tìm thấy biến khớp, không cần tiếp tục duyệt

        final_assigned_tables = [list(set(students)) for students in assigned_tables.values()]
        return final_assigned_tables, total_satisfied_weight

    def get_stats(self):
        """ Trả về các thống kê chính: số biến, số mệnh đề, trọng số và thời gian chạy """
        num_variables = len(self.xij_vars) + len(self.xijk_vars) + len(self.y_vars)
        return {
            'variables': num_variables,
            'hard_clauses': self.hard_count,
            'soft_clauses': self.soft_count,
            'total_weight': self.total_weight,
            'solve_time': self.solve_time
        }

    def print_assigned_tables(self):
        """ In danh sách các bàn đã được sắp xếp """
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
    input_data = 'data/fully/fully_7.txt'
    num_students, preferences = read_data(input_data)
    encoding_type = 'max'

    # Tạo solver và giải bài toán
    solver = TeamCompositionSolver(num_students, preferences, encoding_type=encoding_type)
    solver.solve()
    stats = solver.get_stats()

    # In các thống kê ra
    print(f"Number of variables: {stats['variables']}")
    print(f"Number of hard clauses: {stats['hard_clauses']}")
    print(f"Number of soft clauses: {stats['soft_clauses']}")
    print(f"Total satisfied weight: {stats['total_weight']}")
    print(f"Solve time: {stats['solve_time']:} seconds")

    # # In danh sách bàn đã sắp xếp
    # solver.print_assigned_tables()
