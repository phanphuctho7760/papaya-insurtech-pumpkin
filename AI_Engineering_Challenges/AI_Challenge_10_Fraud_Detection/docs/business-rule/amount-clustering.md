# Amount clustering (khai sát ngưỡng auto-approval)

## Thuật ngữ

- Auto-approval threshold: claim dưới ngưỡng được tự duyệt, không qua người thẩm định. Đề dùng 50,000 (VNĐ).
- Amount clustering: amount dồn sát dưới ngưỡng để né thẩm định.

## Nguồn trong đề

- Dataset: "20 amount clustering (amounts just below the 50,000 auto-approval threshold)".
- Rule 8: "claim amounts within 5% below the 50,000 auto-approval threshold (47,500-49,999)".

## Quy tắc sinh dữ liệu

- Procedure dùng cho clustering: **P-1003 Xét nghiệm nước tiểu**, giá chuẩn 40,000, dao động 15%.
- Claim fraud clustering: P-1003, amount trong 47,500-49,999.
- Không dính upcoding: SD khoảng 6,000 => ngưỡng upcoding khoảng 52,000 > 49,999.
- Claim P-1003 hợp lệ có thể tự rơi vào dải (ước lượng khoảng 6% số claim P-1003); đây là FP tự nhiên có chủ đích, đếm và báo trong metrics.
- Bằng chứng thực tế: giá không BHYT của tổng phân tích nước tiểu ở một bệnh viện công là 48,000 VNĐ (xem `catalog.md`, mục Nguồn), nằm đúng trong dải.
