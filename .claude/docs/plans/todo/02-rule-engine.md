# Plan 02 - B: Engine 8 rule + scoring

> **Ticket:** #02 - trạng thái và mục tiêu nằm ở ticket; file này chỉ chứa chi tiết thực thi.

Nguồn business: `docs/business-rule/detection-rules.md`, `evidence.md`, `scoring.md`, `scoring-weights.md`, `upcoding.md`, `bundling.md`, `diagnosis-procedure-mismatch.md`, `duplicate-and-rapid-resubmission.md`, `weekday-only-providers.md`, `amount-clustering.md`. Kỹ thuật: `docs/decisions/tech-and-structure.md`, `dataset-format.md`. Tên rule: `src/rule_names.py`. Thuật ngữ: `docs/business-rule/glossary.md`.

Phạm vi: engine + CLI `score` + test hệ thống (Phase 4). 19 test business, metrics, test tích hợp thuộc #03.

## Đã chốt trước khi code (2026-10-24)

Người dùng duyệt cả 7 mục theo đề xuất. Đã ghi vào: mục 1, 7 -> `scoring.md`; mục 2 -> `upcoding.md`; mục 3 -> `evidence.md`; mục 4 -> `weekday-only-providers.md`; mục 5 -> `docs/decisions/ADR-002-invalid-input-stops-the-engine.md`, mục 6 -> `ADR-003-only-weights-are-configurable.md`; tất cả -> `challenge-10-requirements.md`.

1. **Mỗi rule tối đa 1 flag cho 1 claim.** Claim dính rapid với 2 claim khác vẫn chỉ 1 flag `rapid_resubmission`, evidence liệt kê mọi claim liên quan. Lý do: score = tổng weight của các rule bị flag (`scoring.md`); 2 flag cùng rule sẽ cộng weight 2 lần.
2. **SD của upcoding: `statistics.pstdev` (độ lệch chuẩn tổng thể).** Lý do: mean/SD tính trên toàn bộ claim cùng mã trong dataset, không phải ước lượng từ mẫu. Với mã >= 44 claim 1 mã, chênh với `stdev` < 1.2%. Điều kiện flag giữ dấu `>` (đề: "> 2 standard deviations"). Evidence ghi số SD = `(amount - mean) / SD`, 1 chữ số thập phân.
3. **Evidence rapid theo chiều thời gian.** Claim sau: `Re-submitted 3 days after CLM-x (2024-03-12) ...` (mẫu `evidence.md`). Claim trước: `Followed 3 days later by CLM-y (2024-03-15) ...`. Cặp cùng ngày khác provider: `Submitted on the same day as CLM-x at another provider PRV-yyy ...`. Bổ sung 2 mẫu này vào `evidence.md`.
4. **"Surgical" của rule weekend:** claim có ít nhất 1 mã trong `procedure_codes` là procedure hoặc bundle có `surgical = true` trong catalog. Ngày cuối tuần lấy từ cột `is_weekend`; tên thứ trong evidence (`Saturday`) suy từ `claim_date`.
5. **Input lỗi thì dừng, không bỏ qua dòng.** Loader kiểm: đúng 10 cột theo thứ tự, `claim_id` duy nhất, ngày hợp lệ, amount số nguyên dương, `is_weekend` 0/1, mọi mã procedure / diagnosis có trong catalog. Bổ sung sau review Phase 1: file là CSV hợp lệ và có >= 1 claim, `claim_id` / `member_id` / `provider_id` không rỗng, `claim_type` thuộc 3 loại, `is_weekend` khớp thứ của `claim_date` (chi tiết: ADR-002). Lỗi => in toàn bộ danh sách lỗi ra stderr, exit 1 (giống `check`). Lý do: rule mismatch / upcoding cho kết quả sai lặng lẽ nếu gặp mã lạ.
6. **Ngưỡng rule là hằng số trong code, không đưa vào config.** Đề chỉ yêu cầu weight cấu hình được. Ngưỡng (7 ngày, 2 SD, 10 claim, 30 claim/ngày, 5%, 50,000 / 47,500) đặt ở đầu file rule tương ứng, evidence đọc từ hằng số (không viết cứng số trong chuỗi).
7. **Format `output/scored_output.json`:** mảng JSON đã xếp hạng, mỗi phần tử đúng 3 trường của đề `claim_id`, `risk_score`, `flags`. Flag trong 1 claim sắp theo severity giảm dần, rồi theo thứ tự `ALL_RULES`. `indent=2`, UTF-8, `ensure_ascii=False`. Không thêm trường ngoài đề (rank, tổng weight) để output khớp ví dụ.

## Phase 1 - Load input và config

**Xong (2026-10-24).** Review 2 vòng; vòng 1 thêm kiểm input (xem mục 5), báo lỗi `csv.Error`, trùng key JSON trong weights. 61 test pass, `data/claims.csv` load đủ 2,000 claim.

- `src/claims.py`: `Claim` (frozen dataclass: 10 trường, `claim_date: date`, `procedure_codes: tuple[str, ...]`, `submitted_amount: int`, `is_weekend: bool`) + `load_claims(path, catalog) -> list[Claim]`, kiểm theo mục 5. Đặt ngang `catalog.py` vì là đầu vào chung của engine và #03.
- `CLAIMS_COLUMNS` chuyển từ `generator/dataset.py` sang `claims.py`; generator import lại. Engine **không** import gì từ `generator/` (generator biết nhãn, engine không được biết).
- `src/config/weights.json`: 8 weight theo `scoring-weights.md`, key = tên trong `ALL_RULES`.
- `src/scoring/weights.py`: `load_weights(path) -> dict[str, int]`. Kiểm: đủ đúng 8 key, không key lạ, giá trị là `int` (không nhận `bool`, `float`) trong 1-5. Lỗi => `WeightsError` liệt kê mọi lỗi (giống `CatalogError`).

## Phase 2 - 8 rule

- `src/rules/<rule>.py`, mỗi file 1 hàm cùng chữ ký: `detect(claims: list[Claim], catalog: Catalog) -> dict[str, str]` (claim_id -> evidence). Rule không biết weight; engine gắn severity.
- `src/rules/__init__.py`: `RULES = {rule_name: detect}` theo thứ tự `ALL_RULES`.
- `src/rules/evidence.py`: helper định dạng chung: `vnd(48500) -> "48,500 VND"`, `code_label("P-3001") -> "P-3001 (Laparoscopic appendectomy)"` (procedure, bundle, diagnosis). Mẫu chuỗi theo `evidence.md`.

| Rule | Cách tính | Ghi chú |
|---|---|---|
| duplicate_claim | Nhóm theo `(member, provider, date, diagnosis)`, nhóm >= 2 => flag cả nhóm | Evidence liệt kê các claim còn lại trong nhóm + số claim của key |
| rapid_resubmission | Nhóm theo `(member, diagnosis)`, sort theo ngày, xét cặp trong nhóm cách 0-7 ngày, bỏ cặp cùng provider + cùng ngày (trùng unique key) | Nhóm chỉ vài claim => không O(n^2) toàn dataset (B5) |
| upcoding | Chỉ claim 1 mã; nhóm theo mã; mã < 10 claim bỏ qua; `amount > mean + 2 x pstdev` | Mã bundle (vd `B-3101` đứng một mình) cũng là 1 mã. SD = 0 => không flag |
| unbundling | Với mỗi bundle: tập thành phần là tập con của `procedure_codes` => flag | Evidence: tổng amount thực khai vs giá gói chuẩn. Dính > 1 bundle => liệt kê hết trong 1 evidence |
| phantom_billing | Đếm theo `(provider, date)`, > 30 => flag mọi claim ngày đó | |
| weekend_anomaly | Tỷ lệ cuối tuần theo provider trên toàn bộ claim; flag claim surgical + cuối tuần + tỷ lệ < 5% | Evidence: `% (k of n claims)` |
| diagnosis_procedure_mismatch | Mã nào trong `procedure_codes` không thuộc `valid_pairs[diagnosis]` => flag | Evidence liệt kê mã sai + danh sách mã hợp lệ |
| amount_clustering | `47,500 <= amount <= 49,999` | % của ngưỡng làm tròn số nguyên |

## Phase 3 - Scoring, xếp hạng, CLI

- `src/scoring/score.py`:
  - `risk_score(total) = round(100 x (1 - e^(-0.25 x total)))`. Đã kiểm total 0-27: không giá trị nào rơi đúng .5 nên `round()` của Python (làm tròn kiểu banker) không gây lệch. total >= 19 => 99, total 27 => 100.
  - `score_claims(claims, catalog, weights) -> list[dict]`: chạy 8 rule, gom flag theo claim, tính score, trả về toàn bộ claim (claim không flag: score 0, `flags: []`).
  - Xếp hạng: `risk_score` giảm dần, rồi số flag giảm dần, rồi `claim_id` tăng dần (`scoring.md`).
- `cli.py score [--data data] [--weights src/config/weights.json] [--out output]`:
  - Chỉ đọc `claims.csv`; không có tham số nào trỏ tới `ground_truth.csv`.
  - `time.perf_counter()` bao quanh load -> rules -> score -> ghi file; in thời gian chạy.
  - In: số claim có flag, số claim theo từng rule, top 10 claim. Ghi `output/scored_output.json`.
- Docstring đầu `cli.py` thêm lệnh `score`; cập nhật hướng dẫn chạy ở `README.md` của project nếu đã có mục chạy lệnh.

## Phase 4 - Test hệ thống (pytest)

Phân biệt 2 loại test (người dùng chốt 2026-10-24):
- **Test hệ thống** (phase này, #02): kiểm code đã implement đúng thiết kế kỹ thuật đã thảo luận (load input, load weights, format output, xếp hạng, ranh giới engine / ground truth). Viết cùng lúc với code.
- **Test business** (19 test trong `docs/business-rule/test-cases.md`, #03): kiểm 8 rule và scoring cho kết quả đúng nghiệp vụ.

File `tests/test_system_*.py`, dữ liệu dựng trong test (không đọc `data/`):

| # | Nhóm | Test | Kết quả mong đợi |
|---|---|---|---|
| S1 | Weights | Weight 0, 6, `"4"`, `true`, `4.0` | `WeightsError`, liệt kê đủ mọi lỗi trong 1 lần |
| S2 | Weights | Thiếu 1 rule / thừa 1 key lạ | `WeightsError` nêu tên rule thiếu / key lạ |
| S3 | Weights | Đổi 1 weight hợp lệ (vd upcoding 4 -> 5) | Score của claim dính rule đó đổi theo, không sửa code |
| S4 | Input | Sai header, trùng `claim_id`, mã procedure / diagnosis lạ, amount không phải số nguyên, `is_weekend` = 2 | Loader báo lỗi, liệt kê đủ |
| S5 | Output | 1 claim không flag, 1 claim nhiều flag | Mọi claim có mặt; mỗi phần tử đúng 3 trường `claim_id`, `risk_score`, `flags`; mỗi flag đúng 3 trường `rule`, `severity`, `evidence` |
| S6 | Output | Claim dính rapid với 2 claim khác | Chỉ 1 flag `rapid_resubmission`, evidence nêu cả 2 claim (mục 1) |
| S7 | Xếp hạng | Các claim bằng điểm, khác số flag / `claim_id` | Đúng thứ tự score -> số flag -> `claim_id`; flag trong claim sắp theo severity |
| S8 | Evidence | Helper `vnd`, `code_label` | `48,500 VND`; `P-3001 (Laparoscopic appendectomy)`, `K02.1 (Dental caries)` |
| S9 | Ranh giới | Quét source `src/claims.py`, `src/rules/`, `src/scoring/` | Không chứa `ground_truth`, không import `generator` |

Thời gian < 30 giây trên dataset thật thuộc test tích hợp của #03.

## Verify

- `uv run pytest` pass toàn bộ test hệ thống S1-S9.
- `score` chạy trên dataset seed 2024: 2,000 phần tử trong output, in thời gian chạy (kỳ vọng < 1 giây).
- Đếm nhanh số claim theo rule, so với số đo thật trong `docs/experiences/dataset-generation-pitfalls.md`: duplicate 30, phantom 31, unbundling 25, weekend 20, mismatch 20, clustering 22 (20 + 2 hợp lệ), rapid 50 (30 + 20 hợp lệ), upcoding 53 (30 + 23 hợp lệ). Lệch => dừng lại tìm nguyên nhân trước khi sang #03.
- Đọc evidence bằng mắt (mở `scored_output.json`, xem tay 1 claim mỗi rule; không phải test tự động): câu dễ hiểu với người thẩm định, đủ 3 phần (quan sát / ngưỡng / claim liên quan), mã có tên tiếng Anh, tiền có dấu phân cách và `VND`.

## Quy trình

- Áp dụng `/pyfriend-claco-bunhy` khi viết code.
- Review diff trước commit; chạy `/pjdoc-mgmt-claco-bunhy pre-commit`.
