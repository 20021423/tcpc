import pandas as pd
import matplotlib.pyplot as plt

# Data for fully satisfied results
data_fully = {
    "filename": [
        "fully_num_7.txt", "fully_num_14.txt", "fully_num_21.txt", "fully_num_28.txt",
        "fully_num_35.txt", "fully_num_42.txt", "fully_num_49.txt", "fully_num_56.txt",
        "fully_num_63.txt", "fully_num_70.txt", "fully_num_77.txt", "fully_num_84.txt",
        "fully_num_91.txt", "fully_num_98.txt", "fully_num_105.txt", "fully_num_112.txt",
        "fully_num_119.txt", "fully_num_126.txt"
    ],
    "num_students": [7, 14, 21, 28, 35, 42, 49, 56, 63, 70, 77, 84, 91, 98, 105, 112, 119, 126],
    "time_sat": [
        0, 0, 0, 0, 0.015637159, 0, 0.015552282, 0.015642405, 0.046793461, 0.031249523,
        0.109471083, 0.066622734, 0.104255676, 0.124168158, 0.12966156, 0.245377064,
        0.416660547, 0.265717745
    ],
    "time_max_rc2": [
        0.001945496, 0.00806284, 0.339703083, 23.92280388, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None
    ],
    "time_min_rc2": [
        0.002161026, 0.001003265, 0.003999949, 0.01095891, 0.019235134, 0.030724525, 0.03870821,
        0.067197323, 0.089046717, 0.146181345, 0.197971106, 0.34612751, 0.316642046, 0.338363171,
        0.597242355, 0.523778439, 1.030810356, 1.128185749
    ],
    "time_max_cpsat": [
        0.017226696, 0.101636887, 0.501900434, 1.659575701, 3.791080952, 6.316955328,
        14.66130304, 17.34234142, 34.25086379, 47.60318303, 65.65426636, 85.22531605,
        119.6599636, 160.7150967, 138.1100798, 257.5648026, 418.0309503, 308.6650515
    ],
    "time_min_cpsat": [
        0.009047031, 0.074251652, 0.436864376, 1.362745762, 2.856876373, 5.310037136,
        11.93607593, 16.55933881, 21.03659201, 27.43237209, 33.94833207, 44.78006077,
        56.41439629, 69.90479064, 93.54416013, 122.3266811, 65.59718037, 207.6768394
    ]
}

# Convert data to DataFrame
df_fully = pd.DataFrame(data_fully)

# Adjust the plot to use specific labels for the x-axis to reflect the exact number of students
plt.figure(figsize=(12, 6))

# Plot for each solver strategy with exact x-axis labels
plt.plot(df_fully["num_students"], df_fully["time_sat"], marker='o', label='MiniSAT')
plt.plot(df_fully["num_students"], df_fully["time_max_rc2"], marker='o', label='RC2 Maximizing')
plt.plot(df_fully["num_students"], df_fully["time_min_rc2"], marker='o', label='RC2 Minimizing')
plt.plot(df_fully["num_students"], df_fully["time_max_cpsat"], marker='o', label='CP-SAT Maximizing')
plt.plot(df_fully["num_students"], df_fully["time_min_cpsat"], marker='o', label='CP-SAT Minimizing')

# Labeling the chart
plt.xlabel("Số lượng học sinh")
plt.ylabel("Thời gian (s)")
plt.yscale('log')  # Use log scale for better readability of time differences
plt.grid(True, which="both", linestyle='--', linewidth=0.5)
plt.legend()

# Set specific x-ticks for each number of students
plt.xticks(df_fully["num_students"], rotation=45)

# Save the figure to a file
output_path = "solver_time_comparison_fully.png"
plt.tight_layout()
plt.savefig(output_path)

# Display the path for the user to download the image
output_path

# Data for partially satisfied results
import pandas as pd
import matplotlib.pyplot as plt

# Data for maximally satisfied results
data_max = {
    "filename": [
        "max_num_7.txt", "max_num_14.txt", "max_num_21.txt", "max_num_28.txt",
        "max_num_35.txt", "max_num_42.txt", "max_num_49.txt", "max_num_56.txt",
        "max_num_63.txt", "max_num_70.txt", "max_num_77.txt", "max_num_84.txt",
        "max_num_91.txt", "max_num_98.txt", "max_num_105.txt", "max_num_112.txt",
        "max_num_119.txt", "max_num_126.txt"
    ],
    "num_students": [7, 14, 21, 28, 35, 42, 49, 56, 63, 70, 77, 84, 91, 98, 105, 112, 119, 126],
    "time_sat": [
        0, 0, 0, 0.001498222, 0, 0, 0.023464561, 0, 0, 0, 0.045025349,
        0.076649666, 0.081764221, 0, 0.139170885, 0, 0, 0.496101379
    ],
    "time_max_rc2": [
        0, 0.005474687, 0.019506454, 234.4582345, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None
    ],
    "time_min_rc2": [
        0.001505256, 0.013007402, 0.022499323, 0.008679152, 0.034015417, 0.05117166,
        0.046876073, 0.143324375, 0.191064, 0.248458385, 0.314524889, 0.308917284,
        0.354528666, 0.822628021, 1.038648605, 1.37782836, 0.884830475, 0.89656353
    ],
    "time_max_cpsat": [
        0.014881968, 0.077714801, 0.308701277, 1.664424181, 4.121644855, 7.507098556,
        14.14662576, 27.616925, 40.91436255, 52.1975019, 63.93998599, 89.24239492,
        142.8205614, 150.745014, 256.2632952, 581.1413047, 119.1600969, 1081.968218
    ],
    "time_min_cpsat": [
        0.013070822, 0.06178093, 0.347658277, 1.462462425, 4.025813937, 6.88400948,
        11.50104904, 18.07368481, 21.53079271, 36.93777728, 39.93189502, 52.38597322,
        65.58626652, 98.79905105, 113.6600063, 128.304213, 159.7676234, 107.3856626
    ]
}

# Convert data to DataFrame
df_max = pd.DataFrame(data_max)

# Adjust the plot to use specific labels for the x-axis to reflect the exact number of students
plt.figure(figsize=(12, 6))

# Plot for each solver strategy with exact x-axis labels
plt.plot(df_max["num_students"], df_max["time_sat"], marker='o', label='MiniSAT')
plt.plot(df_max["num_students"], df_max["time_max_rc2"], marker='o', label='RC2 Maximizing')
plt.plot(df_max["num_students"], df_max["time_min_rc2"], marker='o', label='RC2 Minimizing')
plt.plot(df_max["num_students"], df_max["time_max_cpsat"], marker='o', label='CP-SAT Maximizing')
plt.plot(df_max["num_students"], df_max["time_min_cpsat"], marker='o', label='CP-SAT Minimizing')

# Labeling the chart
plt.xlabel("Số lượng học sinh")
plt.ylabel("Thời gian (s)")
plt.yscale('log')  # Use log scale for better readability of time differences
plt.grid(True, which="both", linestyle='--', linewidth=0.5)
plt.legend()

# Set specific x-ticks for each number of students
plt.xticks(df_max["num_students"], rotation=45)

# Save the figure to a file
output_path = "solver_time_comparison_max.png"
plt.tight_layout()
plt.savefig(output_path)

# Display the path for the user to download the image
output_path
