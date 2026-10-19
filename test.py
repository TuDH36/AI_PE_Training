import os

# =================================================================
# CẤU HÌNH ĐƯỜNG DẪN TẠI ĐÂY
# =================================================================
# Đường dẫn tới file gốc bạn muốn mã hóa
INPUT_FILE = r"E:\AV\Train_AI_Python\Data_Preprocessing\CYAIPENETNEW.mdl" 

# Đường dẫn nơi bạn muốn lưu file đã mã hóa (để sau này đưa vào Resource)
OUTPUT_FILE = r"C:\Users\chien\Downloads\Resource"
# =================================================================

def encrypt_to_folder(input_path, output_folder):
    # 1. Kiểm tra file đầu vào
    if not os.path.exists(input_path):
        print(f"Lỗi: Không tìm thấy file gốc tại {input_path}")
        return

    # 2. Tạo thư mục đầu ra nếu nó chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Đã tạo thư mục mới: {output_folder}")

    # 3. Tự động tạo đường dẫn file đầu ra (Giữ nguyên tên gốc + đuôi .enc)
    file_name = os.path.basename(input_path)
    output_path = os.path.join(output_folder, file_name)

    # 4. Đọc dữ liệu
    with open(input_path, "rb") as f:
        data = f.read()

    i_len = len(data)
    if i_len < 3:
        print("Lỗi: File quá nhỏ.")
        return

    # 5. Logic mã hóa khớp 100% với C++ (Key: HuuTu)
    ORIGINAL_KEY_CONST = 0x4875755475
    key_seed = (ORIGINAL_KEY_CONST ^ i_len) & 0xFF
    
    output_data = bytearray()

    for i in range(i_len):
        key = ((key_seed + i) % i_len) & 0xFF
        val = data[i]

        if i == 0:
            val = (val + key) & 0xFF
        elif i == 1:
            val = (val - key) & 0xFF
        else:
            val = (val ^ key) & 0xFF
            
        output_data.append(val)

    # 6. Ghi file
    with open(output_path, "wb") as f:
        f.write(output_data)
    
    print("-" * 50)
    print(f"THÀNH CÔNG!")
    print(f"File gốc: {file_name}")
    print(f"Đã lưu file mã hóa tại: {output_path}")
    print("-" * 50)

if __name__ == "__main__":
    encrypt_to_folder(INPUT_FILE, OUTPUT_FILE)