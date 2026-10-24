# Diagnosis-procedure mismatch (chẩn đoán không khớp thủ thuật)

## Thuật ngữ

Mismatch: procedure không phù hợp về mặt y khoa với chẩn đoán. Ví dụ chẩn đoán sâu răng (K02.1) nhưng khai mổ ruột thừa (P-3001).

## Nguồn trong đề

- Dataset: "20 diagnosis-procedure mismatches".
- Rule 7: "procedure not clinically associated with diagnosis (provide a mapping of at least 10 valid diagnosis-procedure pairs)".

## Thế nào là "chuẩn": các cặp hợp lệ

Mọi cặp nằm ngoài bảng là mismatch.

| Diagnosis | Procedure / bundle hợp lệ |
|---|---|
| J06.9 | P-1001, P-1002, P-1003, B-1001 |
| I10 | P-1001, P-1002, P-1003, B-1001 |
| E11.9 | P-1001, P-1002, P-1006, B-1002 |
| A09 | P-1001, P-1002, P-1005 |
| N39.0 | P-1001, P-1003 |
| J18.9 | P-1004, P-2001 |
| K35.8 | P-3001, P-3010, B-3101 |
| K80.2 | P-1005, P-3002, P-3010, B-3102 |
| S52.5 | P-3003, P-3010 |
| O80 | P-2002 |
| K02.1 | P-4001, P-4002, P-4003 |
| K04.0 | P-4002, P-4004, B-4101 |

Tổng: 35 cặp (đề yêu cầu >= 10).

Ràng buộc: diagnosis hợp lệ của một bundle phải hợp lệ với **mọi** thành phần của bundle đó, nếu không claim unbundled sẽ dính thêm mismatch. Vì vậy có 3 cặp `J06.9 - P-1003`, `I10 - P-1003` (khám tổng quát có xét nghiệm nước tiểu) và `E11.9 - P-1002` (theo dõi đái tháo đường có công thức máu); thêm ngày 2026-10-24 khi đối chiếu thành phần B-1001, B-1002.

## Quy tắc sinh fraud

- Claim mismatch: chọn diagnosis rồi gán procedure ngoài danh sách hợp lệ của diagnosis đó; amount theo giá chuẩn của procedure (để không dính thêm upcoding). Chọn procedure cùng claim_type, không dùng mã bundle.
