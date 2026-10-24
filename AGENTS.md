# AGENTS.md

## Mục đích

Repo nộp bài test tuyển dụng của Papaya Insurtech. Gồm 2 phần, nộp chung bằng 1 link GitHub/GitLab qua email, hạn 5 ngày kể từ ngày nhận email.

1. **Logical_Questions**: trả lời >= 5 câu, bắt buộc Q1 (ký ức đầu tiên) và Q5 (lần cuối bỏ quên một món đồ).
2. **AI_Engineering_Challenges**: tổng 3 điểm. Đã chọn 1 câu Advanced: **AI Challenge 10 - Fraud Detection Scoring Engine**.

## Cấu trúc

```
.
|-- AGENTS.md                         # file này: tổng quan dự án
|-- .claude/                        # cấu hình agent; docs/plans/ = plan thực thi của Challenge 10 (tài liệu khác nằm trong docs/ của project)
|-- Logical_Questions/                # câu trả lời phần logic, mỗi câu 1 file Q_<n>-<Ten>.md
|-- AI_Engineering_Challenges/
|   `-- AI_Challenge_10_Fraud_Detection/  # project Challenge 10
|       |-- README.md                 # writeup nộp bài (dự kiến)
|       |-- AGENTS.md                 # hướng dẫn riêng cho thiết kế Challenge 10
|       |-- src/                      # source code (dự kiến)
|       `-- conversations/            # log hội thoại AI (bắt buộc nộp, dự kiến)
|           `-- README.md
`-- .tmp/pumpkin-main/                # bản clone repo đề gốc (gitignored, chỉ đọc)
```

## Nguồn tham chiếu

- Đề gốc nằm ở `.tmp/pumpkin-main` (bản clone local). **Không đọc repo GitHub online** `papaya-insurtech/pumpkin`.
- Đề Challenge 10: `.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/AI_Challenge_10.md`
- Quy định chung phần AI: `.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/README.md`
- Quy định phần logic: `.tmp/pumpkin-main/Hiring/Logical_Questions/README.md`
- Handbook của team: `.tmp/pumpkin-main/Software_Artisan_Handbook/`
- **Ghi chú Handbook đã lọc cho Challenge 10: `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/handbook-notes.md`.** Khi người dùng đụng tới chủ đề có trong bảng "Khi nào nhắc" của file này (phân tích đề, so sánh giải pháp, timeline, README, review output AI, domain bảo hiểm, chọn stack, email nộp bài), hãy nhắc ý liên quan.
- **Phân rã yêu cầu Challenge 10: `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/requirements/challenge-10-requirements.md`.** Dùng làm khung A/B/C/D khi bàn chi tiết; cập nhật mục "Quyết định đã chốt" và "Câu hỏi mở" khi có quyết định mới.

## Quy ước làm việc

- Ngôn ngữ trao đổi: tiếng Việt, xưng "tôi" và "bạn". Chỉ dùng ký tự gõ được trên bàn phím (`->`, `-`, `...`, `"`).
- Trả lời ngắn gọn; code ưu tiên dễ đọc hơn trừu tượng.
- Commit theo Conventional Commits (`feat:`, `fix:`, `docs:`, `test:` ...).
- Commit message không thêm dòng `Co-Authored-By` (người dùng chốt 2026-10-24).
- `.tmp/` là tài liệu tham chiếu, không sửa và không commit.
- Phần Logical_Questions là câu trả lời cá nhân của người dùng: agent không tự viết hoặc sửa nội dung trả lời trừ khi được yêu cầu rõ.
