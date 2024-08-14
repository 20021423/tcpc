import os
import pandas as pd
from team_composition_solver import TeamCompositionSolver, read_data
from cpsat_solver import TeamCompositionCPSATSolver, read_data
def run_solver_on_files(data_directory):
    results = []

    for filename in os.listdir(data_directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(data_directory, filename)
            num_students, preferences = read_data(filepath)

            # RC2 Solver with minimizing encoding
            rc2_solver_min = TeamCompositionSolver(num_students, preferences, encoding_type='min')
            rc2_assigned_min, rc2_elapsed_min = rc2_solver_min.solve()
            rc2_total_weight_min = rc2_solver_min.extract_solution_and_calculate_weights(rc2_assigned_min)
            rc2_stats_min = rc2_solver_min.get_stats()

            # CP-SAT Solver with maximizing encoding
            cpsat_solver_max = TeamCompositionCPSATSolver(num_students, preferences, encoding_type='max')
            cpsat_assigned_max, cpsat_elapsed_max = cpsat_solver_max.solve()
            cpsat_total_weight_max = cpsat_solver_max.extract_solution_and_calculate_weights(cpsat_assigned_max)
            cpsat_stats_max = cpsat_solver_max.get_stats()

            # CP-SAT Solver with minimizing encoding
            cpsat_solver_min = TeamCompositionCPSATSolver(num_students, preferences, encoding_type='min')
            cpsat_assigned_min, cpsat_elapsed_min = cpsat_solver_min.solve()
            cpsat_total_weight_min = cpsat_solver_min.extract_solution_and_calculate_weights(cpsat_assigned_min)
            cpsat_stats_min = cpsat_solver_min.get_stats()

            # Collecting results
            result = {
                'num_students': num_students,
                'hard_count_rc2': rc2_stats_min['total_hard_count'],
                'hard_count_cpsat': cpsat_stats_max['hard_clauses'],
                'variables_rc2': rc2_stats_min['variables'],
                'variables_cpsat': cpsat_stats_max['variables'],
                'soft_count_min_rc2': rc2_stats_min['soft_clauses'],
                'soft_count_max_cpsat': cpsat_stats_max['soft_clauses'],
                'soft_count_min_cpsat': cpsat_stats_min['soft_clauses'],
                'time_min_rc2': rc2_elapsed_min,
                'time_max_cpsat': cpsat_elapsed_max,
                'time_min_cpsat': cpsat_elapsed_min,
            }
            results.append(result)

    return results

def export_to_excel(results, output_file):
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"Results have been exported to {output_file}")

if __name__ == "__main__":
    data_directory = 'data/max/temp/'
    output_file = 'solver_results_2.xlsx'

    results = run_solver_on_files(data_directory)
    export_to_excel(results, output_file)
