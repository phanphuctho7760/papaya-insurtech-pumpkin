# Công nghệ và cấu trúc dự án

> Thiết kế dự định, có thể thay đổi trong quá trình làm. Khi thay đổi: cập nhật file này và ghi lý do.

## Công nghệ

| Phần | Công nghệ | Ghi chú |
|---|---|---|
| A. Sinh dataset | Python | Sinh `claims.csv` + `ground_truth.csv`, seed cố định |
| B. Engine (8 rule, scoring) | TypeScript (dự định ban đầu) / đang cân nhắc Python | Đề không yêu cầu API => có thể dùng Python cho cả A và B |

## Ghi chú kỹ thuật (chốt khi implement)

- `config/` là file JSON dùng chung (bundle map, cặp hợp lệ, giá chuẩn, trọng số) để generator và engine không lệch nhau.
- Đề yêu cầu nộp scored output và metrics report => cần lệnh chạy hàng loạt (CLI) xuất ra file; API (nếu có) là phần thêm.

## Cấu trúc `src/`

```
src/
|-- generator/   # sinh dataset + nhãn ground truth (Python)
|-- rules/       # mỗi rule là một hàm thuần, dễ test
|-- config/      # trọng số, bundle map, diagnosis-procedure map
|-- scoring/     # tổng hợp, chuẩn hóa 0-100, xếp hạng
|-- metrics/     # precision, recall, FPR
`-- api/
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
