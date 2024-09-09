# Dự án MaxSAT để giải quyết bài toán sắp xếp chỗ ngồi trong lớp học (TCPC)

## Giới thiệu

Dự án này sử dụng các phương pháp **SAT** và **MaxSAT** để giải quyết **bài toán sắp xếp chỗ ngồi trong lớp học** (Team Composition Problem in a Classroom - TCPC). Bài toán sắp xếp chỗ ngồi thuộc nhóm bài toán NP-khó (NP-Hard) và đòi hỏi các phương pháp tối ưu hóa để tìm kiếm lời giải hợp lý. 

Trong dự án này, chúng ta áp dụng các phương pháp mã hóa **SAT Encoding** và **MaxSAT Encoding**, với các bộ giải như **MiniSAT**, **RC2**, và **CP-SAT**. Dự án cũng bao gồm các thuật toán sinh dữ liệu cho các trường hợp khác nhau để tiến hành thực nghiệm.

## Cấu trúc dự án

### Các tệp mã nguồn chính

- `rc2_tcpc.py`: Mã hóa **MaxSAT Encoding TCPC** với bộ giải **RC2**.
- `cpsat_solver_tcpc.py`: Mã hóa **MaxSAT Encoding TCPC** với bộ giải **CP-SAT**.
- `fully_sat-based_solver.py`: Mã hóa **SAT Encoding TCPC** với bộ giải **MiniSAT**.
- `gen_fully.py`: Thuật toán sinh dữ liệu cho trường hợp fully-satisfied.
- `generate_data.py`: Thuật toán sinh dữ liệu cho trường hợp chung (không fully-satisfied).
- `open-wbo-inc_static`: File biên dịch bộ giải **Open-WBO-Inc**, tuy nhiên hiện tại chưa chạy được do không phù hợp với bài toán này.

### Tệp kết quả thực nghiệm

- `results_final.xlsx`: File kết quả cuối cùng sau khi thực nghiệm với **MaxSAT Encoding** sử dụng các bộ giải **RC2** và **CP-SAT**.
- `sat_results.xlsx`: File kết quả thực nghiệm với **SAT Encoding**.
- `maxsat_results.png`: Hình ảnh kết quả chạy MaxSAT.
- `sat_results.png`: Hình ảnh kết quả chạy SAT.

### Thư mục dữ liệu

- **`data/`**: Chứa các bộ dữ liệu giả lập được sinh ra từ các thuật toán sinh dữ liệu.

### Công cụ và bộ giải được sử dụng
- MiniSAT: Được sử dụng cho SAT Encoding.
- RC2: Được sử dụng cho MaxSAT Encoding.
- CP-SAT: Được sử dụng để giải bài toán với chiến lược Maximizing và Minimizing Encoding.
- Open-WBO-Inc: Đã được biên dịch nhưng chưa chạy được do không phù hợp với bài toán này.

### Tệp cài đặt yêu cầu

- `requirements.txt`: Liệt kê các thư viện Python cần thiết để chạy dự án. Để cài đặt, bạn có thể sử dụng lệnh sau:

```bash
pip install -r requirements.txt

