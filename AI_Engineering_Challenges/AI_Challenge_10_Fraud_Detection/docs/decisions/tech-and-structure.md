# Công nghệ và cấu trúc dự án

> Thiết kế dự định, có thể thay đổi trong quá trình làm. Khi thay đổi: cập nhật file này và ghi lý do.

## Công nghệ (đã chốt 2026-10-24)

| Phần | Công nghệ | Ghi chú |
|---|---|---|
| A. Sinh dataset | Python | Sinh `claims.csv` + `ground_truth.csv`, seed cố định |
| B. Engine (8 rule, scoring) | Python | Cùng ngôn ngữ với A |
| C. Test, metrics | pytest | |

- Thư viện: chỉ thư viện chuẩn (`csv`, `json`, `statistics`, `random`, `datetime`, `math`, `time`) + pytest để test.

### Phương án đã cân nhắc

| Phương án | Lý do không chọn / chọn |
|---|---|
| TypeScript cho B, Python cho A | Không chọn: config phải đọc ở 2 ngôn ngữ, dễ lệch giữa generator và engine. Lợi duy nhất là khớp stack backend của Papaya. |
| **Python cho cả A, B, C** | Chọn: đề không yêu cầu API; 1 nơi đọc config, 1 test runner; Python là stack AI/ML của team (Handbook `Tech_Stack.md`). |
| pandas | Không chọn: 2,000 dòng rất nhỏ; code thuần dễ giải thích từng dòng khi phỏng vấn. |

## Ghi chú kỹ thuật

- `config/` là file JSON dùng chung (bundle map, cặp hợp lệ, giá chuẩn, trọng số) để generator và engine không lệch nhau. Trọng số 1-5 được kiểm khi load.
- Không làm API (đề không yêu cầu). Chạy hàng loạt bằng CLI, xuất file.
- Mọi rule cùng một chữ ký: nhận toàn bộ danh sách claim, trả flag theo `claim_id`. Lý do: 5/8 rule cần nhìn nhiều claim (duplicate, rapid, upcoding, phantom, weekend).
- Hiệu năng (B5): rule rapid chỉ so cặp trong nhóm `(member_id, diagnosis_code)`, mỗi nhóm vài claim => không có O(n^2) trên toàn bộ dataset.
- Đo thời gian (C4): `time.perf_counter()` bao toàn bộ luồng load -> rules -> score -> ghi file trong CLI; ghi kết quả vào metrics report.
- Generator gán `claim_id` sau khi sắp toàn bộ claim theo ngày, để claim fraud không nằm cụm ở cuối dãy ID.

## Cấu trúc `src/`

```
src/
|-- config/      # weights.json, catalog.json (procedure, bundle, giá, cặp hợp lệ)
|-- generator/   # sinh dataset + nhãn ground truth
|-- rules/       # 8 rule, mỗi rule 1 file, hàm thuần
|-- scoring/     # tổng trọng số, chuẩn hóa 0-100, xếp hạng
|-- metrics/     # precision, recall, FPR, report 4 phần
`-- cli.py       # generate | score | metrics
tests/           # pytest
data/            # claims.csv, ground_truth.csv
output/          # scored_output.json, metrics_report.md
```

## Cấu trúc `conversations/`

```
conversations/
|-- README.md                      # mục lục
|-- 00-cowork-analysis.md          # Cowork: phân tích đề, chốt business rule (luôn ở vị trí đầu)
|-- 01-chat-research-domain.md     # Claude Chat
|-- 02-code-phase1-generator.md    # Claude Code
`-- 03-code-phase2-rules.md        # Claude Code
```

- Claude Chat / Cowork: lưu bằng skill `/noteconversaion-clacowo-bunhy` (đang cân nhắc).
- Claude Code: lưu bằng tính năng export.
- Log giữ nguyên văn, không chỉnh sửa.

## Định dạng dữ liệu

Xem `dataset-format.md`.
