# Tiền xử lý và phân loại tệp PE bằng LightGBM

## Giới thiệu

Dự án xây dựng một quy trình tiền xử lý dữ liệu và huấn luyện mô hình học máy để phân loại tệp Windows PE thành hai nhóm:

- `0`: tệp sạch (clean/benign).
- `1`: tệp độc hại (malware/virus).

Toàn bộ quy trình chính nằm trong notebook **`Data_Processing.ipynb`**. Các tệp từ điển đặc trưng và mô hình được tạo ra khi chạy notebook chỉ là đầu ra của quy trình, không phải các mô-đun nguồn độc lập.

> Notebook không đọc hoặc thực thi trực tiếp tệp `.exe`/`.dll`. Đầu vào là các tệp `.data` dạng văn bản đã được trích xuất đặc trưng trước đó.

## Nội dung chính của notebook

Quy trình trong `Data_Processing.ipynb` gồm các bước sau:

1. **Chuẩn bị dữ liệu**
   - Đọc danh sách tệp sạch và tệp malware từ các thư mục được cấu hình.
   - Gán nhãn `0` cho dữ liệu sạch và `1` cho malware.
   - Chia dữ liệu thành 80% huấn luyện và 20% kiểm thử với `random_state=42`.
   - Có thể bổ sung thêm dữ liệu sạch vào tập huấn luyện.

2. **Đọc và chuẩn hóa mẫu**
   - Mỗi tệp `.data` được đọc với encoding `latin-1`.
   - Các trường dữ liệu được phân tách bằng ký tự tab (`\t`).
   - Một số định dạng cũ hoặc thiếu trường được chèn thêm 256 giá trị `0.0` để tương thích với cấu trúc đặc trưng hiện tại.

3. **Xử lý đặc trưng số**
   - Lấy 775 trường đầu tiên của mỗi mẫu.
   - Chuyển toàn bộ giá trị sang kiểu `float`.

4. **Xử lý tên section của PE**
   - Đọc danh sách tên section, chuyển về chữ thường và giữ tối đa 10 section.
   - Mẫu có ít hơn 10 section được bổ sung bằng token `null`.
   - Xây dựng từ điển theo tần suất xuất hiện và ánh xạ tên section sang số nguyên.
   - Từ điển có thể được lưu vào `PE64Section` để dùng lại đúng thứ tự đặc trưng.

5. **Xử lý DLL và hàm import**
   - Chuẩn hóa tên DLL, tên API, ordinal và hậu tố decorated như `@8`, `@12`.
   - Giảm nhiễu từ các thư viện CRT/toolchain.
   - Nhận diện các nhóm hành vi đáng chú ý như nạp thư viện động, thao tác bộ nhớ, process/thread, registry, network và crypto.
   - Tính thống kê theo nhãn, gồm tần suất tài liệu, xác suất malware khi token xuất hiện và điểm Chi-square.
   - Chọn tối đa 5.000 token import có giá trị phân biệt cao và lưu thứ tự token vào `PE64DICT`.
   - Bổ sung 13 đặc trưng tổng hợp, ví dụ số import, số DLL, số ordinal, tỷ lệ CRT và các cờ hành vi.

6. **Tạo vector cuối cùng**
   - Ghép ba nhóm đặc trưng theo đúng thứ tự:

     ```text
     775 đặc trưng số + 10 section + K token import + 13 đặc trưng import tổng hợp
     ```

   - Với `K` là số token thực tế trong `PE64DICT`, số chiều đầu vào là `798 + K`.

7. **Huấn luyện và đánh giá**
   - Sử dụng `lightgbm.LGBMClassifier` với tối đa 1.000 cây.
   - Áp dụng early stopping sau 50 vòng không cải thiện trên tập validation.
   - Đánh giá bằng Accuracy, Precision, Recall và F1-score theo macro average.
   - Mô hình chính được lưu dưới dạng LightGBM text model tại `CYAIPE64.txt`.

8. **Kiểm thử bổ sung**
   - Tiền xử lý một tập dữ liệu độc lập bằng cùng từ điển và cùng thứ tự đặc trưng.
   - In danh sách các mẫu dự đoán sai để phục vụ phân tích false positive/false negative.
   - Notebook cũng có các cell thử nghiệm mức độ quan trọng và loại bỏ đặc trưng.

## Kết quả tham khảo

Output đang được lưu trong notebook ghi nhận một lần chạy PE64 với 84.504 mẫu huấn luyện:

| Chỉ số | Giá trị |
|---|---:|
| Best iteration | 229 |
| Accuracy | 0,9948 |
| Precision (macro) | 0,9938 |
| Recall (macro) | 0,9939 |
| F1-score (macro) | 0,9938 |

Trên tập kiểm tra độc lập chỉ gồm 5.733 mẫu sạch, notebook ghi nhận 25 mẫu bị dự đoán nhầm là malware, tương ứng accuracy khoảng 99,56%. Precision/Recall/F1 macro trên một tập chỉ có một lớp không phản ánh đầy đủ chất lượng mô hình; nên sử dụng tập kiểm thử chứa cả hai lớp để so sánh mô hình.

Các số liệu trên chỉ mang tính tham khảo và có thể thay đổi theo dữ liệu, từ điển đặc trưng, phiên bản thư viện và thứ tự cell được chạy.

## Yêu cầu môi trường

Notebook lưu metadata của Python 3.11. Các thư viện chính gồm:

- Jupyter
- NumPy
- scikit-learn
- LightGBM

Khởi tạo môi trường trên Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install jupyter numpy scikit-learn lightgbm
```

## Chuẩn bị dữ liệu

Có thể tổ chức dữ liệu bên ngoài repository theo cấu trúc gợi ý sau:

```text
dataset/
├── Clean64/             # Dữ liệu sạch dùng để train/test
├── Virus64/             # Dữ liệu malware dùng để train/test
├── AdditionalClean64/   # Dữ liệu sạch bổ sung (nếu có)
├── TestClean64/         # Tập sạch độc lập
└── TestMalware64/       # Tập malware độc lập
```

Mỗi mẫu phải là một tệp `.data` dạng văn bản, chứa các trường đặc trưng phân tách bằng tab. Luồng PE64 mong đợi tối thiểu 776 trường sau bước tương thích/padding:

- Chỉ số `0..774`: đặc trưng số.
- Chỉ số `775`: chuỗi tên section.
- Từ chỉ số `776`: thông tin DLL và hàm import.

## Cách chạy

1. Mở `Data_Processing.ipynb` và cập nhật các đường dẫn ở phần đầu notebook:

   ```python
   PATH_Virus = r"<đường-dẫn-tới-Virus64>"
   PATH_Clean = r"<đường-dẫn-tới-Clean64>"
   PATH_ADD_XTest = r"<đường-dẫn-tới-AdditionalClean64>"
   ```

2. Nếu kiểm thử trên dữ liệu độc lập, cập nhật thêm `MAL_DIR` và `CLEAN_DIR` trong phần kiểm thử.

3. Khởi động Jupyter:

   ```powershell
   jupyter lab .\Data_Processing.ipynb
   ```

4. Restart kernel, sau đó chạy tuần tự các cell thuộc luồng PE64: nạp dữ liệu, xử lý section, xử lý import, ghép vector, huấn luyện và đánh giá.

## Lưu ý quan trọng

- Notebook hiện chứa một số cell thử nghiệm cũ cho .NET và PE32. Các cell này định nghĩa lại một số hàm của PE64, vì vậy **không nên chọn Run All** nếu chưa tách hoặc vô hiệu hóa chúng. Với luồng PE64, bỏ qua các khối có tiêu đề `Phần chạy cho Net` và các khối kết quả PE32/.NET.
- Các đường dẫn trong notebook đang là đường dẫn tuyệt đối trên Windows; cần thay bằng đường dẫn dữ liệu trên máy đang chạy.
- Thứ tự của `PE64Section`, `PE64DICT` và vector huấn luyện phải được giữ cố định. Khi dự đoán, luôn dùng đúng các từ điển đã đi kèm lúc huấn luyện mô hình.
- Token section chưa biết hiện có thể được thêm vào từ điển trong lúc vector hóa. Để tái lập kết quả và triển khai ổn định, nên đóng băng từ điển sau khi xây dựng trên tập train và ánh xạ token lạ về một ID `unknown` cố định.
- Cần kiểm tra số mẫu, số nhãn và số chiều feature trước khi huấn luyện. Mẫu thiếu hoặc sai định dạng có thể làm dữ liệu và nhãn không còn khớp nhau.
- Không thực thi các mẫu PE không rõ nguồn gốc. Quy trình này chỉ cần làm việc với dữ liệu đặc trưng đã được trích xuất.

## Đầu ra của quy trình

Khi chạy luồng PE64, notebook có thể tạo hoặc cập nhật:

| Tệp | Vai trò |
|---|---|
| `PE64Section` | Từ điển tên section và thứ tự ánh xạ |
| `PE64DICT` | Từ điển token DLL/API import |
| `CYAIPE64.txt` | Mô hình LightGBM đã huấn luyện |

Ba tệp trên phải được quản lý cùng nhau để bảo đảm quá trình dự đoán sử dụng đúng không gian đặc trưng của mô hình.
