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
        self.variable_count = 0  # To track the total number of variables
        self._initialize_variables()

    def _initialize_variables(self):
        """ Initialize Boolean variables for the formula. """
        for i in range(1, self.num_students + 1):
            for j in range(i + 1, self.num_students + 1):
                self.xij_vars[(i, j)] = self.model.NewBoolVar(f'xij_{i}_{j}')
                self.variable_count += 1  # Increment the variable count
            for j in range(i + 1, self.num_students + 1):
                for k in range(j + 1, self.num_students + 1):
                    self.xijk_vars[(i, j, k)] = self.model.NewBoolVar(f'xijk_{i}_{j}_{k}')
                    self.variable_count += 1  # Increment the variable count
            self.y_vars[i] = self.model.NewBoolVar(f'y_{i}')
            self.variable_count += 1  # Increment the variable count

    def add_hard_clauses(self):
        """ Add hard constraints to the model. """
        self._add_single_assignment_clauses()
        self._add_valid_table_clauses()
        self._add_cardinality_constraint()

    def _add_single_assignment_clauses(self):
        """ Add constraints ensuring each student is assigned to exactly one table. """
        for i in range(1, self.num_students + 1):
            clause = self._get_single_assignment_clause(i)
            self.model.Add(sum(clause) == 1)
            self.hard_count += 1

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
        return clause

    def _add_valid_table_clauses(self):
        """ Add constraints ensuring valid table assignments. """
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
        """ Add cardinality constraints for the number of tables. """
        num_tables_2 = int(self.num_students * 4 / 7)
        self.model.Add(sum(self.y_vars.values()) == num_tables_2)
        self.hard_count += 1

    def calculate_weights(self):
        """ Calculate weights based on the student preferences. """
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
        """ Add soft constraints to the model based on encoding type. """
        if self.encoding_type == 'min':
            self._add_soft_clauses_minimizing(wij, wijk)
        elif self.encoding_type == 'max':
            self._add_soft_clauses_maximizing(wij, wijk)
        else:
            raise ValueError("Invalid encoding type. Use 'min' for minimizing or 'max' for maximizing.")

    def _add_soft_clauses_minimizing(self, wij, wijk):
        """ Add soft constraints to the model based on minimizing encoding using precomputed wij and wijk. """
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
        """ Add soft constraints for maximizing encoding. """
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
        """ Solve the model using CP-SAT solver. """
        self.add_hard_clauses()
        wij, wijk = self.calculate_weights()
        self.add_soft_clauses(wij, wijk)

        solver = cp_model.CpSolver()
        start_time = time.time()
        status = solver.Solve(self.model)
        elapsed_time = time.time() - start_time

        assigned_tables = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for (i, j), var in self.xij_vars.items():
                if solver.Value(var):
                    assigned_tables.append(sorted([i, j]))
            for (i, j, k), var in self.xijk_vars.items():
                if solver.Value(var):
                    assigned_tables.append(sorted([i, j, k]))

        return assigned_tables, elapsed_time

    def extract_solution_and_calculate_weights(self, assigned_tables):
        """ Calculate the total satisfied weights based on the assigned tables. """
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
        """ Retrieve statistics for the current formula. """
        return {
            'hard_clauses': self.hard_count,
            'soft_clauses': self.soft_count,
            'variables': self.variable_count,
        }

def read_data(filename):
    """ Read student preferences from a file. """
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_students = int(lines[0].strip())
    preferences = {}
    for line in lines[1:]:
        parts = list(map(int, line.strip().split()))
        preferences[parts[0]] = parts[1:]

    return num_students, preferences

if __name__ == "__main__":
    input_data = 'data/max/students_preferences_119.txt'
    num_students, preferences = read_data(input_data)

    solver = TeamCompositionCPSATSolver(num_students, preferences, encoding_type='min')
    assigned_tables, elapsed_time = solver.solve()
    # total_weight = solver.extract_solution_and_calculate_weights(assigned_tables)
    stats = solver.get_stats()

    # Print the results
    print("Assigned tables:")
    for table in assigned_tables:
        print(table)
    print(f"Students: {num_students}")
    print(f"Time: {elapsed_time:} seconds")
    # print(f"Total weight: {total_weight}")
    print(f"Hard clauses: {stats['hard_clauses']}")
    print(f"Soft clauses: {stats['soft_clauses']}")
    print(f"Variables: {stats['variables']}")
