# Catalog: procedure, bundle, giá chuẩn

Dữ liệu tham chiếu dùng chung cho generator (mục A) và engine (mục B).

## Vai trò của bảng giá

- Đây là bài test: bảng giá là **ví dụ giả lập**. Trong thực tế, insurer / TPA đã có bảng giá chính thức.
- Mục tiêu của bảng giá ở đây: mức giá **hợp lý** và **không làm dữ liệu phá rule** (vd claim hợp lệ không tự vượt ngưỡng upcoding, claim clustering không dính upcoding). Độ chính xác so với thị trường là thứ yếu.

## Quy ước chung

- Đơn vị tiền: **VNĐ**, giữ nguyên các con số của đề (ngưỡng auto-approval 50,000 VNĐ).
- Mặt bằng giá: **bệnh viện / phòng khám tư** tại Việt Nam (bảo hiểm sức khỏe tư nhân thường dùng ở cơ sở tư).
- Mã chẩn đoán: ICD-10 thật, xem `icd-10.md`. Mã procedure và mã bundle: tự đặt.
- Claim hợp lệ có **đúng 1 mã** trong `procedure_codes` (có thể là mã procedure lẻ hoặc mã bundle). Claim nhiều mã chỉ xuất hiện ở fraud unbundling.
- Amount claim hợp lệ = giá chuẩn x hệ số ngẫu nhiên log-normal, dao động khoảng 15%.

## Thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| Procedure | Dịch vụ / thủ thuật y tế đã thực hiện (khám, xét nghiệm, phẫu thuật...) |
| Surgical | Procedure thuộc loại phẫu thuật |
| Bundle (gói) | Nhóm procedure luôn đi cùng nhau, tính bằng 1 mã gói, rẻ hơn tổng giá lẻ |
| Giá chuẩn | Giá tham chiếu của procedure, tâm của phân phối amount claim hợp lệ |
| Dao động | Mức amount claim hợp lệ lệch quanh giá chuẩn (15% => phần lớn trong khoảng giá chuẩn +-15%) |

## Thuật ngữ đánh giá (metrics)

So kết quả engine với ground truth (đáp án đúng: claim nào thực sự là fraud):

| Thuật ngữ | Nghĩa | Ví dụ |
|---|---|---|
| TP (True Positive) | Engine flag, claim **là** fraud | Bắt đúng claim upcoded |
| **FP (False Positive)** - báo nhầm | Engine flag, nhưng claim **không phải** fraud | Claim xét nghiệm nước tiểu hợp lệ giá 48,000 bị flag amount clustering |
| FN (False Negative) - bỏ sót | Engine không flag, nhưng claim **là** fraud | Claim weekend fraud không bị bắt vì tỷ lệ cuối tuần của provider vượt 5% |
| TN (True Negative) | Engine không flag, claim không phải fraud | Claim hợp lệ bình thường |
| Precision | TP / (TP + FP): trong các claim bị flag, bao nhiêu % đúng là fraud | |
| Recall | TP / (TP + FN): trong các claim fraud, bắt được bao nhiêu % | Đề yêu cầu >= 70% |
| FPR (False Positive Rate) | FP / (FP + TN): trong các claim hợp lệ, bao nhiêu % bị báo nhầm | Đề yêu cầu <= 20% |

FP tự nhiên: claim hợp lệ tự rơi vào điều kiện của rule (không do chèn fraud). Dataset cho phép FP tự nhiên có chủ đích để metrics trung thực; số lượng được đếm và báo trong metrics report.

## Procedure

| Mã | Procedure | claim_type | Giá chuẩn (VNĐ) | Surgical |
|---|---|---|---|---|
| P-1001 | Khám bệnh | OUTPATIENT | 200,000 | |
| P-1002 | Xét nghiệm máu (công thức máu) | OUTPATIENT | 100,000 | |
| P-1003 | Xét nghiệm nước tiểu | OUTPATIENT | 40,000 | |
| P-1004 | X-quang ngực | OUTPATIENT | 150,000 | |
| P-1005 | Siêu âm bụng | OUTPATIENT | 250,000 | |
| P-1006 | Xét nghiệm HbA1c | OUTPATIENT | 150,000 | |
| P-2001 | Điều trị nội trú viêm phổi | INPATIENT | 10,000,000 | |
| P-2002 | Sinh thường | INPATIENT | 30,000,000 | |
| P-3001 | Mổ ruột thừa nội soi | INPATIENT | 18,000,000 | x |
| P-3002 | Cắt túi mật nội soi | INPATIENT | 25,000,000 | x |
| P-3003 | Phẫu thuật kết hợp xương | INPATIENT | 22,000,000 | x |
| P-3010 | Gây mê | INPATIENT | 3,000,000 | |
| P-4001 | Khám răng | DENTAL | 100,000 | |
| P-4002 | X-quang răng | DENTAL | 80,000 | |
| P-4003 | Trám răng | DENTAL | 400,000 | |
| P-4004 | Điều trị tủy | DENTAL | 2,000,000 | |

## Bundle (5 gói)

Giá gói khoảng 90% tổng giá lẻ. Chi tiết rule: `bundling.md`.

| Mã gói | Tên | Thành phần | Tổng giá lẻ | Giá gói | Surgical |
|---|---|---|---|---|---|
| B-1001 | Khám tổng quát | P-1001 + P-1002 + P-1003 | 340,000 | 305,000 | |
| B-1002 | Khám đái tháo đường | P-1001 + P-1002 + P-1006 | 450,000 | 405,000 | |
| B-3101 | Gói mổ ruột thừa | P-3001 + P-3010 | 21,000,000 | 19,000,000 | x |
| B-3102 | Gói cắt túi mật | P-3002 + P-3010 | 28,000,000 | 25,500,000 | x |
| B-4101 | Gói điều trị tủy | P-4002 + P-4004 | 2,080,000 | 1,900,000 | |

## Provider

- 50 provider, 3 loại: bệnh viện (nội trú, phẫu thuật), phòng khám (ngoại trú), nha khoa (răng).
- 10 bệnh viện weekday-only: xem `weekday-only-providers.md`.

## Nguồn tham khảo giá

Bảng giá là giả lập. Phần lớn giá chuẩn là ước lượng từ kiến thức chung; các mục sau có đối chiếu nguồn (research ngày 2026-10-24, nhiều nguồn là bảng giá cũ hoặc blog tổng hợp):

| Mã | Nguồn tìm được | Ghi chú |
|---|---|---|
| P-1002 | Công 46,200-70,000; tư 98,000 (DIAG) | Hạ về 100,000 cho sát giá tư |
| P-1003 | Công 27,400-28,600 (BHYT), 48,000 (không BHYT) | Tư chưa có nguồn; 48,000 rơi đúng dải clustering |
| P-1006 | Công 101,000-143,000; tư 120,000-150,000 | Khớp |
| P-2002 | Tư 27-45 triệu (Vinmec, Tâm Anh) | Đặt 30 triệu theo mặt bằng tư |
| P-3001 | Tư 8-30 triệu (Long Châu) | Khớp |
| P-4003 | 150,000-500,000 | Khớp |

Link nguồn:
- BV Phụ sản Hải Phòng: https://benhvienphusanhaiphong.vn/Images/news/Bảng%20giá%20viện%20phí%20khám%20chữa%20bệnh.pdf
- NQ 45/2024 Hà Nội: https://storage-vnportal.vnpt.vn/gov-hni/6249/VanBanCongBao/2025/3/28/NQPQ-45-2025-23_signed.pdf
- Medpro (xét nghiệm máu): https://medpro.vn/tin-tuc/xet-nghiem-mau-bao-nhieu-tien
- Pharmacity (HbA1c): https://www.pharmacity.vn/xet-nghiem-hba1c-gia-bao-nhieu.htm
- Vinmec sinh thường (qua Medpro): https://medpro.vn/tin-tuc/chi-phi-sinh-o-vinmec-bao-nhieu
- Tâm Anh sinh trọn gói: https://tamanhhospital.vn/sinh-con-tron-goi/
- Long Châu (mổ ruột thừa): https://nhathuoclongchau.com.vn/bai-viet/thac-mac-chi-phi-mo-ruot-thua-bao-nhieu-tien-69480.html
- Medpro (trám răng): https://medpro.vn/tin-tuc/gia-tram-rang-bao-nhieu-tien
