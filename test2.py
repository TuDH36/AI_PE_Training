import os
import hashlib

# =================================================================
# CẤU HÌNH TẠI ĐÂY
# =================================================================
# 1. File ĐÃ MÃ HÓA (file .enc bạn vừa tạo ra)
INPUT_ENC_FILE = r"C:\Users\chien\Downloads\Resource\CYAIPE32NEW.mdl" 

# 2. Thư mục chứa kết quả giải mã (ResourceDe)
OUTPUT_FOLDER = r"C:\Users\chien\Downloads\ResourceDe"

# 3. (Tùy chọn) File gốc ban đầu để đối chiếu (nếu muốn script tự kiểm tra khớp hay không)
ORIGINAL_FILE = r"E:\AV\Train_AI_Python\Data_Preprocessing\CYAIPE32NEW.mdl"
# =================================================================

def decrypt_test(enc_path, output_folder, original_path=None):
    if not os.path.exists(enc_path):
        print(f"Lỗi: Không tìm thấy file mã hóa tại {enc_path}")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Tự động tạo đường dẫn file đầu ra (bỏ đuôi .enc đi để về tên gốc)
    file_name = os.path.basename(enc_path).replace(".enc", "")
    output_path = os.path.join(output_folder, "DECRYPTED_" + file_name)

    with open(enc_path, "rb") as f:
        enc_data = f.read()

    i_len = len(enc_data)
    
    # Logic giải mã khớp 100% với hàm C++ DecryptBuffer
    ORIGINAL_KEY_CONST = 0x4875755475
    key_seed = (ORIGINAL_KEY_CONST ^ i_len) & 0xFF
    
    decrypted_data = bytearray()

    for i in range(i_len):
        key = ((key_seed + i) % i_len) & 0xFF
        val = enc_data[i]

        # GIẢI MÃ: ĐẢO NGƯỢC LOGIC MÃ HÓA
        if i == 0:
            val = (val - key) & 0xFF # Đảo của + là -
        elif i == 1:
            val = (val + key) & 0xFF # Đảo của - là +
        else:
            val = (val ^ key) & 0xFF # XOR là nghịch đảo của chính nó
            
        decrypted_data.append(val)

    with open(output_path, "wb") as f:
        f.write(decrypted_data)
    
    print("-" * 50)
    print(f"THÀNH CÔNG: Đã giải mã file ra {output_path}")

    # TỰ ĐỘNG KIỂM TRA KHỚP VỚI FILE GỐC (Hash MD5)
    if original_path and os.path.exists(original_path):
        with open(original_path, "rb") as f:
            orig_hash = hashlib.md5(f.read()).hexdigest()
        with open(output_path, "rb") as f:
            new_hash = hashlib.md5(f.read()).hexdigest()
        
        if orig_hash == new_hash:
            print("KẾT QUẢ: KHỚP 100%! Logic giải mã đã chuẩn xác.")
        else:
            print("KẾT QUẢ: KHÔNG KHỚP! Hãy kiểm tra lại logic.")
    print("-" * 50)

if __name__ == "__main__":
    decrypt_test(INPUT_ENC_FILE, OUTPUT_FOLDER, ORIGINAL_FILE)