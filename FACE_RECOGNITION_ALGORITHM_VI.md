# Thuật Toán Nhận Diện Khuôn Mặt - Tài Liệu Kỹ Thuật

## Mục Lục
1. [Tổng Quan](#tổng-quan)
2. [Kiến Trúc Thuật Toán](#kiến-trúc-thuật-toán)
3. [Phát Hiện Khuôn Mặt](#phát-hiện-khuôn-mặt)
4. [Nhận Diện Khuôn Mặt](#nhận-diện-khuôn-mặt)
5. [Quy Trình Huấn Luyện](#quy-trình-huấn-luyện)
6. [Luồng Nhận Diện](#luồng-nhận-diện)
7. [Thông Số Kỹ Thuật](#thông-số-kỹ-thuật)
8. [Tối Ưu Hóa Hiệu Suất](#tối-ưu-hóa-hiệu-suất)

---

## Tổng Quan

Hệ thống nhận diện khuôn mặt này sử dụng **OpenCV** với thuật toán **LBPH (Local Binary Patterns Histograms)** để nhận diện khuôn mặt và **Haar Cascade Classifiers** để phát hiện khuôn mặt. Sự kết hợp này được tối ưu hóa cho Raspberry Pi và cung cấp sự cân bằng tốt giữa độ chính xác và hiệu suất.

### Tại Sao Chọn LBPH?
- **Nhẹ**: Chạy hiệu quả trên Raspberry Pi
- **Không Phụ Thuộc Bên Ngoài**: Chỉ sử dụng OpenCV
- **Độ Chính Xác Tốt**: Đáng tin cậy trong môi trường được kiểm soát
- **Huấn Luyện Nhanh**: Có thể huấn luyện lại nhanh chóng khi thêm khuôn mặt mới
- **Bộ Nhớ Thấp**: Yêu cầu tài nguyên tối thiểu

---

## Kiến Trúc Thuật Toán

```
┌─────────────────────────────────────────────────────────────┐
│              HỆ THỐNG NHẬN DIỆN KHUÔN MẶT                   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼────────┐     ┌───────▼────────┐
        │ Phát Hiện      │     │ Nhận Diện      │
        │ Khuôn Mặt      │     │ Khuôn Mặt      │
        │ (Haar Cascade) │     │     (LBPH)     │
        └────────────────┘     └─────────────────┘
                │                       │
        ┌───────▼────────┐     ┌───────▼────────┐
        │ Tiền Xử Lý     │     │ Mã Hóa         │
        │ - Xám          │     │ Khuôn Mặt      │
        │ - Tỷ lệ        │     │ - Đặc trưng LBP│
        │ - Kích thước   │     │ - Histogram    │
        └─────────────────┘     │ - So sánh      │
                                └─────────────────┘
```

---

## Phát Hiện Khuôn Mặt

### 1. Bộ Phân Loại Haar Cascade

**Haar Cascade là gì?**
- Phương pháp phát hiện đối tượng dựa trên học máy
- Sử dụng hàm cascade được huấn luyện từ hình ảnh dương và âm
- Phát hiện khuôn mặt bằng cách tìm kiếm các đặc trưng cụ thể (cạnh, đường, mẫu)

**Quy Trình:**

```python
# 1. Tải bộ phân loại Haar Cascade đã được huấn luyện
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# 2. Chuyển đổi hình ảnh sang xám (xử lý nhanh hơn)
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# 3. Phát hiện khuôn mặt
faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,      # Tỷ lệ giảm kích thước ảnh ở mỗi cấp độ
    minNeighbors=5,       # Số lượng hàng xóm mỗi hình chữ nhật cần có
    minSize=(30, 30)      # Kích thước khuôn mặt tối thiểu để phát hiện
)
```

### 2. Các Tham Số Phát Hiện

| Tham Số | Giá Trị | Mô Tả |
|---------|---------|-------|
| **scaleFactor** | 1.1 | Tỷ lệ giảm kim tự tháp ảnh (1.05 - 1.4) |
| **minNeighbors** | 5 | Số lượng hàng xóm tối thiểu (thường 3-6) |
| **minSize** | (30, 30) | Kích thước khuôn mặt tối thiểu tính bằng pixel |

**Cách hoạt động:**

1. **Kim Tự Tháp Ảnh**: Tạo nhiều cấp độ kích thước của ảnh
   ```
   Gốc (640x480) → 580x435 → 527x395 → ...
   ```

2. **Cửa Sổ Trượt**: Di chuyển cửa sổ phát hiện qua mỗi cấp độ
   ```
   ┌─────────────────────┐
   │    ┌──┐            │
   │    └──┘→           │  Quét toàn bộ ảnh
   │                    │
   └─────────────────────┘
   ```

3. **Phát Hiện Đặc Trưng**: Tìm kiếm đặc trưng khuôn mặt ở mỗi vị trí
   - Vùng mắt (tối)
   - Sống mũi (sáng)
   - Vùng miệng (tối)

4. **Lọc Hàng Xóm**: Kết hợp các phát hiện chồng chéo
   ```
   Nhiều phát hiện → Nhóm gần nhau → Một khung mặt
   ```

### 3. Kết Quả Phát Hiện Khuôn Mặt

Trả về danh sách các hộp giới hạn:
```python
faces = [(x, y, w, h), ...]
# x, y: Tọa độ góc trên-trái
# w, h: Chiều rộng và chiều cao của hình chữ nhật khuôn mặt
```

**Ví dụ:**
```
┌─────────────────────────────┐
│                             │
│     ┌───────────────┐      │
│     │   x,y         │      │  Khuôn mặt phát hiện tại (150, 100)
│     │       👤      │      │  Kích thước: 200x200 pixels
│     │               │      │
│     └───────────────┘      │
│                             │
└─────────────────────────────┘
```

---

## Nhận Diện Khuôn Mặt

### 1. Thuật Toán LBPH (Local Binary Patterns Histograms)

**LBPH là gì?**

LBPH là bộ mô tả kết cấu tạo ra dấu vân tay độc nhất cho mỗi khuôn mặt bằng cách phân tích các mẫu cục bộ.

**Quy Trình:**

#### Bước 1: Chia Khuôn Mặt Thành Các Ô
```
Khuôn Mặt Gốc (200x200)
┌─────────────────────┐
│  ┌───┬───┬───┬───┐ │
│  │ 1 │ 2 │ 3 │ 4 │ │  Chia thành lưới
│  ├───┼───┼───┼───┤ │  (ví dụ: 8x8 ô)
│  │ 5 │ 6 │ 7 │ 8 │ │
│  ├───┼───┼───┼───┤ │
│  │ 9 │10 │11 │12 │ │
│  └───┴───┴───┴───┘ │
└─────────────────────┘
```

#### Bước 2: Tính LBP Cho Mỗi Pixel

Với mỗi pixel, so sánh với 8 hàng xóm:
```
    Hàng Xóm          Nhị Phân        Giá Trị LBP
    88  95  102        0  0  1
    90 [100] 108  →    0  ●  1    →   01011100₂ = 92
    75  80   95        0  0  1
```

**Thuật Toán:**
```python
center = giá_trị_pixel
for hàng_xóm in 8_hàng_xóm:
    if hàng_xóm >= center:
        giá_trị_nhị_phân = 1
    else:
        giá_trị_nhị_phân = 0
LBP = nối_tất_cả_giá_trị_nhị_phân → thập_phân
```

#### Bước 3: Tạo Histogram

Cho mỗi ô, tạo histogram của các giá trị LBP:
```
Histogram Ô:
Giá trị:  0   1   2  ...  92  ... 255
Số lượng: [5] [3] [8] ... [12] ... [4]
          └────────────────────────────┘
                256 bins
```

#### Bước 4: Nối Tất Cả Histogram

```
Vector Đặc Trưng Cuối Cùng:
[Hist_Ô1] + [Hist_Ô2] + ... + [Hist_Ô64]
= 256 × 64 = 16,384 chiều
```

### 2. Quy Trình Nhận Diện

**Giai Đoạn Huấn Luyện:**
```python
# Với mỗi người dùng đã đăng ký
for người_dùng in danh_sách_người_dùng:
    # 1. Tải tất cả ảnh khuôn mặt
    ảnh = tải_ảnh_người_dùng(người_dùng)
    
    # 2. Trích xuất đặc trưng LBP
    đặc_trưng = []
    for ảnh in danh_sách_ảnh:
        đặc_trưng_lbp = tính_lbp(ảnh)
        đặc_trưng.append(đặc_trưng_lbp)
    
    # 3. Huấn luyện mô hình LBPH
    mô_hình.train(đặc_trưng, nhãn)
```

**Giai Đoạn Nhận Diện:**
```python
# 1. Phát hiện khuôn mặt trong khung hình
vùng_mặt = phát_hiện_khuôn_mặt(khung_hình)

# 2. Trích xuất đặc trưng LBP
đặc_trưng_test = tính_lbp(vùng_mặt)

# 3. So sánh với mô hình đã huấn luyện
nhãn, độ_tin_cậy = mô_hình.predict(đặc_trưng_test)

# 4. Đưa ra quyết định
if độ_tin_cậy < 70:  # Thấp hơn là tốt hơn với LBPH
    tên = danh_sách_tên[nhãn]
else:
    tên = "Không xác định"
```

### 3. Điểm Độ Tin Cậy

**Độ Tin Cậy LBPH:**
- **Thấp hơn = Khớp Tốt Hơn** (ngược với thông thường)
- **Phạm Vi:** 0 đến ~150+
- **Ngưỡng:**
  - `< 50`: Khớp xuất sắc
  - `50-70`: Khớp tốt ✓ (ngưỡng của chúng ta)
  - `70-90`: Khớp trung bình
  - `> 90`: Khớp kém (Không xác định)

**Tại sao độ tin cậy ngược?**
Độ tin cậy LBPH biểu diễn khoảng cách giữa các histogram:
```
Khoảng cách = √Σ(histogram1 - histogram2)²
```
Khoảng cách nhỏ hơn = giống nhau hơn = khớp tốt hơn

---

## Quy Trình Huấn Luyện

### 1. Luồng Đăng Ký

```
Đăng Ký Người Dùng
    │
    ├─> 1. Chụp Nhiều Mẫu (5 ảnh)
    │        │
    │        ├─> Ảnh 1 (mặt ở giữa)
    │        ├─> Ảnh 2 (nghiêng trái nhẹ)
    │        ├─> Ảnh 3 (nghiêng phải nhẹ)
    │        ├─> Ảnh 4 (ánh sáng bình thường)
    │        └─> Ảnh 5 (biểu cảm khác)
    │
    ├─> 2. Phát Hiện Khuôn Mặt Trong Mỗi Mẫu
    │        └─> Sử dụng Haar Cascade
    │
    ├─> 3. Trích Xuất Vùng Khuôn Mặt (ROI)
    │        └─> Thay đổi kích thước thành 200x200 pixels
    │
    ├─> 4. Chuyển Sang Ảnh Xám
    │        └─> Loại bỏ thông tin màu
    │
    ├─> 5. Lưu Mẫu Vào Ổ Đĩa
    │        └─> data/images/{tên}/sample_*.jpg
    │
    └─> 6. Huấn Luyện Mô Hình LBPH
         └─> Cập nhật bộ nhận diện
```

### 2. Thuật Toán Huấn Luyện

```python
def huấn_luyện():
    mã_hóa = []
    nhãn = []
    tên = []
    
    # Với mỗi thư mục người dùng
    for tên_người_dùng in thư_mục_người_dùng:
        # Lấy nhãn người dùng (chỉ số)
        if tên_người_dùng not in tên:
            tên.append(tên_người_dùng)
        nhãn_người_dùng = tên.index(tên_người_dùng)
        
        # Xử lý mỗi ảnh
        for tệp_ảnh in ảnh_người_dùng:
            # Tải ảnh
            ảnh = cv2.imread(tệp_ảnh)
            
            # Phát hiện khuôn mặt
            xám = cv2.cvtColor(ảnh, cv2.COLOR_BGR2GRAY)
            mặt = face_cascade.detectMultiScale(xám, 1.3, 5)
            
            # Trích xuất khuôn mặt đầu tiên
            (x, y, w, h) = mặt[0]
            vùng_mặt = xám[y:y+h, x:x+w]
            
            # Thay đổi kích thước thành kích thước chuẩn
            vùng_mặt = cv2.resize(vùng_mặt, (200, 200))
            
            # Thêm vào tập huấn luyện
            mã_hóa.append(vùng_mặt)
            nhãn.append(nhãn_người_dùng)
    
    # Huấn luyện mô hình LBPH
    bộ_nhận_diện = cv2.face.LBPHFaceRecognizer_create()
    bộ_nhận_diện.train(mã_hóa, np.array(nhãn))
    
    return bộ_nhận_diện, tên
```

### 3. Cấu Trúc Lưu Trữ

```
data/
├── images/
│   ├── John/
│   │   ├── sample_1.jpg  ← 200x200 ảnh xám
│   │   ├── sample_2.jpg
│   │   ├── sample_3.jpg
│   │   ├── sample_4.jpg
│   │   └── sample_5.jpg
│   ├── Mary/
│   │   ├── sample_1.jpg
│   │   └── ...
│   └── ...
└── faces/
    └── encodings.pkl  ← Mô hình đã tuần tự hóa (tùy chọn)
```

---

## Luồng Nhận Diện

### Quy Trình Nhận Diện Hoàn Chỉnh

```
┌──────────────────────────────────────────────────────────┐
│ 1. CHỤP KHUNG HÌNH                                       │
│    Camera → ảnh BGR 640x480                             │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 2. CHUYỂN SANG ẢNH XÁM                                   │
│    BGR → Xám (xử lý nhanh hơn)                          │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 3. PHÁT HIỆN KHUÔN MẶT                                   │
│    Haar Cascade → Danh sách (x, y, w, h)                │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 4. TRÍCH XUẤT VÙNG KHUÔN MẶT                             │
│    Cắt vùng mặt → Thay đổi kích thước thành 200x200     │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 5. TÍNH ĐẶC TRƯNG LBP                                    │
│    LBPH.predict() → nhãn, độ_tin_cậy                     │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 6. SO SÁNH ĐỘ TIN CẬY                                    │
│    if độ_tin_cậy < 70: KHỚP                              │
│    else: KHÔNG XÁC ĐỊNH                                  │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ 7. TRẢ VỀ KẾT QUẢ                                        │
│    tên = "John" hoặc "Không xác định"                    │
└──────────────────────────────────────────────────────────┘
```

### Ví Dụ Code

```python
def nhận_diện_người(khung_hình):
    # 1. Chuyển sang ảnh xám
    xám = cv2.cvtColor(khung_hình, cv2.COLOR_BGR2GRAY)
    
    # 2. Phát hiện khuôn mặt
    mặt = face_cascade.detectMultiScale(
        xám,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    kết_quả = []
    
    # 3. Xử lý mỗi khuôn mặt phát hiện được
    for (x, y, w, h) in mặt:
        # Trích xuất vùng khuôn mặt
        vùng_mặt = xám[y:y+h, x:x+w]
        
        # Thay đổi kích thước thành kích thước chuẩn
        vùng_mặt = cv2.resize(vùng_mặt, (200, 200))
        
        # 4. Dự đoán danh tính
        nhãn, độ_tin_cậy = bộ_nhận_diện.predict(vùng_mặt)
        
        # 5. Kiểm tra ngưỡng độ tin cậy
        if độ_tin_cậy < 70:
            tên = danh_sách_tên[nhãn]
            kết_quả.append((tên, độ_tin_cậy, (x, y, w, h)))
        else:
            kết_quả.append(("Không xác định", độ_tin_cậy, (x, y, w, h)))
    
    return kết_quả
```

---

## Thông Số Kỹ Thuật

### Yêu Cầu Hệ Thống

| Thành Phần | Thông Số |
|-----------|---------|
| **Vi Xử Lý** | Raspberry Pi 3/4 hoặc tương đương |
| **RAM** | Tối thiểu 1GB |
| **Camera** | Pi Camera hoặc USB Webcam |
| **Độ Phân Giải** | Tối thiểu 640x480 |
| **Tốc Độ Khung Hình** | 15-30 FPS |

### Chỉ Số Hiệu Suất

| Chỉ Số | Giá Trị |
|--------|---------|
| **Tốc Độ Phát Hiện** | ~30ms mỗi khung hình |
| **Tốc Độ Nhận Diện** | ~10ms mỗi khuôn mặt |
| **Thời Gian Huấn Luyện** | ~2s cho 10 người × 5 ảnh |
| **Bộ Nhớ Sử Dụng** | ~50MB cho 50 người đã đăng ký |
| **Độ Chính Xác** | ~90-95% trong ánh sáng được kiểm soát |

### Điều Chỉnh Tham Số

#### Tham Số Phát Hiện

```python
# Điều chỉnh cho môi trường
DETECTION_SCALE_FACTOR = 1.1   # 1.05 = chậm hơn nhưng chính xác hơn
                               # 1.3  = nhanh hơn nhưng có thể bỏ lỡ mặt

DETECTION_MIN_NEIGHBORS = 5    # 3 = phát hiện nhiều hơn (dương tính giả)
                               # 7 = phát hiện ít hơn (bỏ lỡ một số mặt)

DETECTION_MIN_SIZE = (30, 30)  # Kích thước khuôn mặt tối thiểu
                               # Nhỏ hơn = phát hiện mặt xa
                               # Lớn hơn = bỏ qua mặt nhỏ
```

#### Tham Số Nhận Diện

```python
# Ngưỡng độ tin cậy
CONFIDENCE_THRESHOLD = 70      # Thấp hơn = khớp chặt chẽ hơn
                               # Cao hơn = khớp lỏng hơn

# Kích thước khuôn mặt
FACE_SIZE = (200, 200)         # Kích thước khuôn mặt chuẩn
                               # Lớn hơn = chi tiết hơn nhưng chậm hơn
                               # Nhỏ hơn = nhanh hơn nhưng ít chính xác
```

---

## Tối Ưu Hóa Hiệu Suất

### 1. Tối Ưu Xử Lý Khung Hình

**Xử Lý Mỗi Khung Hình Thứ N:**
```python
đếm_khung = 0
PROCESS_EVERY_N_FRAMES = 2  # Xử lý mỗi khung thứ 2

while True:
    khung = camera.read()
    đếm_khung += 1
    
    if đếm_khung % PROCESS_EVERY_N_FRAMES == 0:
        # Thực hiện phát hiện/nhận diện khuôn mặt
        kết_quả = nhận_diện_khuôn_mặt(khung)
    
    # Luôn hiển thị (sử dụng kết quả đã lưu)
    hiển_thị_kết_quả(khung, kết_quả)
```

**Lợi Ích:**
- Xử lý nhanh hơn 2 lần
- Mất độ chính xác tối thiểu
- Hiển thị video mượt mà hơn

### 2. Tiền Xử Lý Ảnh

**Chuyển Đổi Sang Ảnh Xám:**
```python
xám = cv2.cvtColor(khung, cv2.COLOR_BGR2GRAY)
```
- Giảm dữ liệu 66% (3 kênh → 1)
- Phát hiện cascade nhanh hơn
- Sử dụng bộ nhớ ít hơn

**Thay Đổi Kích Thước Khuôn Mặt:**
```python
vùng_mặt = cv2.resize(vùng_mặt, (200, 200))
```
- Chuẩn hóa kích thước đầu vào
- Trích xuất đặc trưng nhất quán
- Tính toán LBP nhanh hơn

### 3. Huấn Luyện Đa Mẫu

**Tại Sao 5 Mẫu Mỗi Người?**
- **1 mẫu:** Độ chính xác kém, không có biến thể
- **3 mẫu:** Phủ sóng cơ bản
- **5 mẫu:** Cân bằng tốt ✓
- **10+ mẫu:** Tốt hơn nhưng huấn luyện chậm hơn

**Chiến Lược Chụp Mẫu:**
```python
mẫu = [
    "Mặt ở giữa",          # Tham chiếu cơ bản
    "Nghiêng trái nhẹ",    # Biến thể góc
    "Nghiêng phải nhẹ",    # Biến thể góc
    "Biểu cảm khác",       # Biến thể biểu cảm
    "Ánh sáng khác"        # Biến thể ánh sáng
]
```

### 4. Quản Lý Bộ Nhớ

**Tải Lười Biếng:**
```python
# Không giữ tất cả ảnh trong bộ nhớ
def huấn_luyện():
    for tệp_ảnh in danh_sách_tệp_ảnh:
        ảnh = cv2.imread(tệp_ảnh)  # Tải
        mã_hóa = xử_lý(ảnh)         # Xử lý
        del ảnh                      # Giải phóng bộ nhớ
```

**Lưu Trữ Mô Hình:**
```python
# Lưu mô hình đã huấn luyện để tránh huấn luyện lại
bộ_nhận_diện.write('model.yml')

# Tải khi cần
bộ_nhận_diện = cv2.face.LBPHFaceRecognizer_create()
bộ_nhận_diện.read('model.yml')
```

---

## Khắc Phục Sự Cố

### Các Vấn Đề Thường Gặp

| Vấn Đề | Nguyên Nhân | Giải Pháp |
|--------|------------|-----------|
| **Không phát hiện được mặt** | Ánh sáng kém | Cải thiện ánh sáng, điều chỉnh minNeighbors |
| **Nhận diện sai người** | Đặc trưng tương tự | Huấn luyện lại với nhiều mẫu hơn |
| **Điểm độ tin cậy cao** | Chất lượng ảnh kém | Cải thiện chất lượng camera, ánh sáng |
| **Hiệu suất chậm** | Xử lý mỗi khung | Sử dụng PROCESS_EVERY_N_FRAMES |
| **Lỗi bộ nhớ** | Quá nhiều người dùng | Triển khai lưu trữ mô hình |

### Cải Thiện Độ Chính Xác

1. **Ánh Sáng:** Ánh sáng nhất quán, đều là quan trọng
2. **Góc Độ:** Mặt hướng thẳng vào camera
3. **Khoảng Cách:** 1-2 mét là tối ưu
4. **Mẫu:** Nhiều mẫu hơn = độ chính xác tốt hơn
5. **Chất Lượng:** Độ phân giải cao hơn = đặc trưng tốt hơn

---

## Tài Liệu Tham Khảo

### Tài Liệu OpenCV
- Haar Cascade: https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html
- LBPH: https://docs.opencv.org/4.x/df/d25/tutorial_face_landmark_detector_in_opencv.html

### Bài Báo Nghiên Cứu
- Phát Hiện Khuôn Mặt Viola-Jones (2001)
- Nhận Diện Khuôn Mặt LBPH (Ahonen và cộng sự, 2006)

### Tệp Triển Khai
- `face_detector.py` - Triển khai Haar Cascade
- `face_recognizer.py` - Triển khai nhận diện LBPH
- `config.py` - Cấu hình tham số

---

**Cập Nhật Lần Cuối:** 10 Tháng 1, 2026
**Phiên Bản:** 1.0
