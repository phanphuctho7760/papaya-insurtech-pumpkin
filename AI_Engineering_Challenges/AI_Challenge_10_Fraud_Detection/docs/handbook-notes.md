# Handbook notes cho Challenge 10 (Chat / Cowork)

Tóm tắt các phần trong Software_Artisan_Handbook (repo papaya-insurtech/pumpkin, không kèm trong project) dùng được khi làm AI Challenge 10 - Fraud Detection Scoring Engine.
Phạm vi: chỉ phần áp dụng cho Claude Chat và Claude Cowork. Phần Claude Code xem mục "Để dành cho Claude Code" ở cuối.

> Cho agent: khi người dùng chạm tới chủ đề trong bảng "Khi nào nhắc" dưới đây, hãy nhắc ngắn gọn ý liên quan và dẫn đường file gốc.

## Khi nào nhắc

| Người dùng đang làm | Nhắc mục |
|---|---|
| Đọc đề, phân tích yêu cầu, liệt kê chỗ mơ hồ | 1, 2 |
| Chọn hướng giải pháp, thiết kế, so sánh phương án | 1, 2 |
| Ước lượng timeline | 2 |
| Viết README, writeup, mô tả cách dùng AI | 3 |
| Commit, đặt tên branch | 3 |
| Review code / output do AI sinh ra | 4 |
| Đặt tên field, viết evidence, giải thích trọng số rule | 5 |
| Chọn ngôn ngữ / stack | 6 |
| Soạn email nộp bài | 7 |

## 1. AI Agent Philosophy

Nguồn Handbook: `Software_Artisan_Handbook/resources/AI_Agent_Workflow/AI_Agent_Philosophy.md`

- Three-tool model: Chat = research, brainstorm, rubber-duck, nhờ tìm lỗi giải pháp. Cowork = phân tích yêu cầu, test plan, tài liệu. Code = viết code, git, test.
- Ask What and Why before How: đưa context What/Why, để agent đề xuất How; nếu đã có hướng thì đưa như gợi ý, yêu cầu agent đánh giá rủi ro và so sánh phương án.
- Review plans more than raw code: người review 100% plan/spec/assumption; agent review code trước, người tập trung vùng rủi ro (business logic, chỗ agent tự giả định).
- Autonomous is not Automation: engine rule-based là automation; AI chỉ dùng để thiết kế và xây nó.
- Iterate, don't restart; Stay in control.

Liên hệ đề: Papaya chấm "decompose the problem, direct the AI tool effectively" và bắt buộc nộp log hội thoại AI nguyên văn. Cách làm việc với AI cũng là đối tượng bị chấm.

## 2. Task Lifecycle

Nguồn Handbook: `Software_Artisan_Handbook/resources/Development_Process/resources/Task_Lifecycle.md`

- New Task: description phải rõ What + Why. Dán đề vào Chat để tìm ambiguity, thông tin thiếu.
- Research: không nhảy vào code ngay; giải pháp phải end-to-end, bao hết use case.
- Solution Review: luôn đưa ra >= 2 giải pháp kèm pros/cons; task phức tạp thì có diagram. Dùng Cowork soạn tài liệu so sánh, Chat để pressure-test.
- Code priorities: [1] chạy đúng, [2] sạch, dễ đọc, đúng convention, [3] tối ưu.
- Có thể dùng các phase này làm khung timeline mà đề yêu cầu ước lượng.

## 3. Reviewee Convention

Nguồn Handbook: `Software_Artisan_Handbook/resources/Development_Process/resources/Code_Review/resources/Reviewee_Convention.md`

- Mục "Agent Workflow" trong mô tả: agent nào đã dùng, các prompt/chỉ đạo chính, đã tự kiểm tra gì, giới hạn còn lại. Nên đưa vào README nộp bài.
- Commit theo Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` ...
- Branch: `feat/`, `fix/`, `docs/`, `test/` ...
- Mô tả có checklist việc đã làm + summary What/Why.

## 4. Reviewing AI Generated Code + Code Review Checklist

Nguồn Handbook: `Software_Artisan_Handbook/resources/Development_Process/resources/Code_Review/resources/Reviewing_AI_Generated_Code.md`, `.../Code_Review_Checklist.md`

Checklist tự review output AI:
- Hallucinated API: import, signature có thật không.
- Scope creep: mọi thay đổi phải truy về yêu cầu của đề.
- Wrong business logic: thuật ngữ, luồng claim đúng chưa; hỏi "có hợp lý với nghiệp vụ không", không chỉ "có chạy không".
- Over-engineering: có phải giải pháp đơn giản nhất không.
- Không để lại TODO, placeholder (lưu ý: dataset synthetic là yêu cầu của đề, không phải mock thừa).
- Code sạch: không code thừa, không code comment-out, không print debug; comment chỉ để giải thích WHY / TODO / Warning.
- Phải có test.

## 5. Medical Insurance 101 (domain)

Nguồn Handbook: `Software_Artisan_Handbook/resources/Medical_Insurance_101.md`

- Thực thể: Policy Owner, Insured Person, Medical Provider (CSYT), Insurer, TPA.
- Claim method: Reimbursement (theo chi phí thực tế, có trần Limit) và Lump Sum.
- Health claim: Cashless / Direct Billing và Reimbursement Claim.
- Tiền: Sum Insured / Limit, Balance, Deductible, Co-payment.
- Dùng để đặt tên, viết evidence, giải thích trọng số rule đúng ngữ cảnh bảo hiểm (vd ngưỡng auto-approval 50,000 gắn với luồng thẩm định claim).
- KHÔNG có: fraud pattern, ICD-10, procedure code, bundling. Phần này cần research riêng.

## 6. Tech Stack

Nguồn Handbook: `Software_Artisan_Handbook/resources/Tech_Stack.md`

- AI/ML của team: Python (Pytorch, Keras, OpenAI, Vertex AI, Gemini). Backend: Node.js / TypeScript.

## 7. Communication Convention (chỉ cho email nộp bài)

Nguồn Handbook: `Software_Artisan_Handbook/resources/Communication_Convention.md`

- Email trang trọng; subject dạng `[Project Name] Subject`; luôn có greeting, sign-off, signature; nhắc tới đính kèm / link trong thân email.

## Bỏ qua

Git_Workflow (Gitflow nhiều nhánh môi trường), Release_Process, System_Environment, Monorepo, VS_Code_Recommended_Extensions, OS_Softwares_And_Tools.

## Để dành cho Claude Code (đọc khi chuyển sang Claude Code)

- `Software_Artisan_Handbook/resources/AI_Agent_Workflow/Claude_Code_Best_Practices.md`: prompting, Plan Mode, session management.
- `Software_Artisan_Handbook/resources/AI_Agent_Workflow/Claude_Code_Workflow_Setup.md`: Superpowers flow, branch/worktree/PR, harness, reviewer agents.
- `Software_Artisan_Handbook/resources/AI_Agent_Workflow/Agent_Troubleshooting.md`: loop, hallucination, context limit, scope creep, khi nào restart.
- Các mục "With Claude Code" trong Git_Workflow và phase Coding / Testing / Code Review của Task_Lifecycle.
