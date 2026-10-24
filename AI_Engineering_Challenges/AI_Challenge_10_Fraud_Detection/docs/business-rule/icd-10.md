# ICD-10 và mã procedure

## ICD-10 là gì

- ICD-10 (International Classification of Diseases, 10th Revision) là bộ phân loại bệnh quốc tế do WHO ban hành, dùng để mã hóa chẩn đoán.
- Trong claim bảo hiểm sức khỏe, `diagnosis_code` cho biết người được bảo hiểm (Insured Person) được chẩn đoán bệnh gì; insurer/TPA dựa vào đó để thẩm định quyền lợi và chi phí.
- Cấu trúc mã: 1 chữ cái + 2 chữ số (nhóm bệnh), có thể thêm dấu chấm và 1-2 chữ số chi tiết.
  - Ví dụ: `J06.9` - nhiễm trùng đường hô hấp trên cấp, không xác định; `I10` - tăng huyết áp nguyên phát; `E11` - đái tháo đường type 2; `K02` - sâu răng.
- Chữ cái đầu cho biết chương bệnh (vd `J` hô hấp, `I` tuần hoàn, `K` tiêu hóa, `E` nội tiết).

## Vì sao dùng ICD-10 thật

- Đề yêu cầu cột `diagnosis_code` là "ICD-10 code".
- Dùng mã thật giúp evidence của rule đọc được theo ngữ cảnh y khoa (vd "procedure P-2001 không phù hợp với chẩn đoán K02 - sâu răng").

## Mã procedure

- Đề không chỉ định chuẩn mã procedure; ví dụ output của đề dùng mã dạng `P-1234`.
- Dataset dùng mã procedure tự đặt theo dạng `P-xxxx`, mỗi mã có: tên, giá chuẩn, cờ surgical.

## Phạm vi bộ mã trong dataset

- Bộ mã nhỏ và khép kín: khoảng 10-15 mã ICD-10 phổ biến và bộ procedure tương ứng.
- Lý do: rule diagnosis-procedure mismatch coi mọi cặp không nằm trong danh sách hợp lệ là mismatch; bộ mã khép kín giúp claim hợp lệ chỉ dùng cặp hợp lệ.
- Danh sách mã cụ thể: xem `catalog.md`.

## Bộ mã ICD-10 dùng trong dataset (12 mã)

| Mã | Chẩn đoán | claim_type |
|---|---|---|
| J06.9 | Nhiễm trùng hô hấp trên cấp | OUTPATIENT |
| I10 | Tăng huyết áp nguyên phát | OUTPATIENT |
| E11.9 | Đái tháo đường type 2, không biến chứng | OUTPATIENT |
| A09 | Viêm dạ dày ruột nhiễm trùng | OUTPATIENT |
| N39.0 | Nhiễm trùng đường tiết niệu | OUTPATIENT |
| J18.9 | Viêm phổi | INPATIENT |
| K35.8 | Viêm ruột thừa cấp | INPATIENT |
| K80.2 | Sỏi túi mật | INPATIENT |
| S52.5 | Gãy đầu dưới xương quay | INPATIENT |
| O80 | Sinh thường | INPATIENT |
| K02.1 | Sâu răng (ngà) | DENTAL |
| K04.0 | Viêm tủy răng | DENTAL |

## Tên tiếng Anh (dùng trong evidence)

| Mã | English name |
|---|---|
| J06.9 | Acute upper respiratory infection |
| I10 | Essential hypertension |
| E11.9 | Type 2 diabetes without complications |
| A09 | Infectious gastroenteritis |
| N39.0 | Urinary tract infection |
| J18.9 | Pneumonia |
| K35.8 | Acute appendicitis |
| K80.2 | Gallstones |
| S52.5 | Fracture of lower end of radius |
| O80 | Normal delivery |
| K02.1 | Dental caries |
| K04.0 | Pulpitis |
