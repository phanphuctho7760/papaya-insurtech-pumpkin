# Plan 03 - C: Unit test, metrics, đo thời gian

> **Ticket:** #03 - trạng thái và mục tiêu nằm ở ticket; file này chỉ chứa chi tiết thực thi.

Nguồn business: `docs/business-rule/test-cases.md` (19 test + test tích hợp), `metrics.md` (định nghĩa, 4 phần report), `fraud-injection.md` (ngoại lệ phantom day), `glossary.md` mục Evaluation. Kỹ thuật: `docs/decisions/tech-and-structure.md` (cây `src/metrics/`, C4 timing). Số đo cần đối chiếu: `docs/experiences/dataset-generation-pitfalls.md`.

Phạm vi: 19 test business, module + CLI `metrics`, `output/metrics_report.md`, test tích hợp trên `data/` thật, cập nhật pitfalls doc. Không đụng logic rule / scoring (nếu test lộ bug engine => dừng, báo người dùng, không tự sửa trong ticket này). Writeup README thuộc #04.

## Số đo sơ bộ (2026-10-25, script nháp đọc `output/scored_output.json` + `ground_truth.csv`)

- TP 200, FP 46, FN 0, TN 1,754 => precision 81.3%, recall 100%, FPR 2.6%. Đạt cả 2 mục tiêu.
- Theo pattern: 8/8 pattern bắt đủ (vd upcoding 30/30).
- Natural FP theo rule: rapid 24, upcoding 18, clustering 4 => khớp mục 1, 3, 8 của pitfalls doc.
- Fraud dính thêm rule ngoài pattern: đúng 6 claim, đều là `phantom_billing` trên phantom day (3 upcoding + 3 mismatch) => khớp ngoại lệ đã ghi.
- Bảng ngưỡng: > 0 -> recall 100% / FPR 2.6%; >= 40 -> 80% / 2.3%; >= 70 -> 18% / 0%.

Số này là kỳ vọng cho Verify; code thật phải ra đúng như vậy.

## Đã chốt trước khi code (2026-10-25)

Người dùng duyệt cả 6 mục theo đề xuất. Đã ghi vào: mục 1 -> `metrics.md`; tất cả -> `challenge-10-requirements.md` (Settled decisions, C1-C4).

1. **Ngưỡng trong bảng phần 4:** 3 dòng `score > 0` (>= 1 flag, = metric chính), `score >= 40`, `score >= 70`. `metrics.md` ghi "ngưỡng 0" => sửa câu chữ thành `> 0` cho khỏi hiểu nhầm `>= 0` (flag mọi claim). Với weight hiện tại score chỉ nhận các giá trị rời rạc (39, 53, 63, 71, ...) nên `>` hay `>=` ở 40 / 70 cho cùng kết quả; chọn `>=` vì đọc tự nhiên hơn ("từ 40 điểm trở lên").
2. **Lệnh `metrics` chạy lại cả pipeline score rồi mới so ground truth.** `cli.py metrics [--data data] [--weights ...] [--out output]`: load -> 8 rule -> score -> ghi `scored_output.json` (đo thời gian đoạn này, giống `score`) -> đọc `ground_truth.csv` -> ghi `metrics_report.md`. Tách phần chung của `cmd_score` thành 1 hàm `run_score(args) -> (results, elapsed)` để 2 lệnh dùng chung.
   - Phương án bị loại: `metrics` chỉ đọc `scored_output.json` có sẵn. Lý do loại: thời gian chạy không nằm trong output (output chỉ 3 trường của đề) => report không có số đo thật, hoặc phải ghi thời gian ra file phụ.
   - Thời gian = 1 lần chạy, `time.perf_counter()` trong process (không tính khởi động Python); report ghi rõ phạm vi đo.
3. **`src/metrics/` được đọc ground truth, engine thì không.** `src/metrics/evaluate.py` (đếm TP/FP/FN/TN, theo pattern, FP theo rule, bảng ngưỡng: hàm thuần trên list) + `src/metrics/report.py` (dựng markdown). Engine không import `metrics`; S9 hiện quét `claims.py`, `rules/`, `scoring/` nên không cần sửa. Ground truth đọc bằng hàm riêng trong `metrics/`, kiểm tối thiểu: header `claim_id,is_fraud,fraud_pattern`, tập `claim_id` khớp đúng tập claim đã score (lệch => dừng, exit 1, giống ADR-002).
4. **Natural FP theo rule:** 1 claim FP dính 2 rule thì đếm cho cả 2 rule; bảng có thêm dòng tổng số claim FP (46) để người đọc không cộng cột ra 46 sai. Mỗi rule ghi: số flag, số flag trên claim fraud, số flag trên claim legit (FP).
5. **Ngoại lệ trong test tích hợp suy từ dữ liệu, không viết cứng claim_id:** claim fraud nằm trên `phantom_provider_day` (đọc từ `generation_summary.json`) được phép dính thêm `phantom_billing`. Mọi rule thừa khác => test fail, message liệt kê `claim_id`, pattern, các rule thừa. Test được đọc ground truth (test không phải engine).
6. **Format `output/metrics_report.md`:** tiếng Anh (như mọi file output). Đầu file: dataset (số claim, số fraud, seed), weight đang dùng, thời gian chạy. Sau đó 4 phần theo `metrics.md`, mỗi phần là 1 bảng markdown, % lấy 1 chữ số thập phân, mỗi bảng có 1-2 câu đọc số (vd "recall 100% vì dataset sinh ra theo đúng định nghĩa rule, xem phần hạn chế ở README"). Nội dung tất định trừ dòng thời gian.

## Phase 1 - 19 test business

- File `tests/test_business_rules.py`, mỗi dòng của `test-cases.md` = 1 hàm `test_tcNN_<mô tả>` (NN = số trong bảng), docstring ghi lại kết quả mong đợi của bảng.
- Unit level: gọi thẳng `RULES[rule](claims, catalog)` với claim dựng trong test (giống `make_claim` ở `test_system_rules_contract.py`; có thể chuyển helper này sang `tests/conftest.py` nếu dùng chung, không đổi hành vi test cũ). Không đọc `data/`.
- Kiểm cả claim nào bị flag lẫn claim nào không (vd TC1: đúng 2 claim trong cặp, không dư claim khác); evidence chỉ kiểm có số / mã then chốt, không so nguyên câu (câu đã có test ở #02).
- Dữ liệu cụ thể:
  - TC6 / TC7 upcoding: 1 mã có 10 claim (9 claim cùng amount + 1 claim vượt mean + 2 SD) => flag; cùng bố cục với 9 claim => không flag.
  - TC10 / TC11 phantom: 31 / 30 claim cùng provider + ngày.
  - TC12 weekend: provider có 30 claim, 1 claim cuối tuần (3.3%), claim đó có mã surgical (vd P-3001). TC13: cùng tỷ lệ, claim cuối tuần không surgical.
  - TC16 / TC17 clustering: 4 claim với amount 47,500 / 49,999 / 47,499 / 50,000.
  - TC18: `risk_score(6) == 78` và 1 claim dính mismatch (4) + clustering (2) qua `score_claims` => score 78, 2 flag.
  - TC19: claim sạch qua `score_claims` => score 0, `flags == []`.
- Spec giao cho `coder`; sau đó `reviewer` (diff + phase này).

**Xong (2026-10-25).** Review 2 vòng. Vòng 1 bổ sung fixture, vẫn giữ đúng 19 hàm: TC12 thêm provider đúng 5% (trước đó điều kiện < 5% chưa có test nào kiểm); TC06 thêm claim giữa 1-2 SD, claim nhiều mã, outlier nằm giữa ngưỡng `pstdev` / `stdev`; 3 assert evidence luôn đúng được siết lại. Vòng 2: TC07 dùng fixture riêng (outlier lệch 2.83 SD), vì helper mới làm TC07 pass kể cả khi `MIN_CLAIMS` = 9. 132 test pass. Mutation đều bị bắt: phantom `>=`, rapid 8 ngày, weekend tỷ lệ 1.0 / `>`, SD 1 / 2.5, `stdev`, bỏ lọc 1 mã, `MIN_CLAIMS` 9 / 11, 4 biên clustering. Chấp nhận còn lọt: upcoding `>` -> `>=` (cần amount bằng đúng ngưỡng số thực).
- Bẫy khi chạy mutation: sau khi hoàn tác, `.pyc` cũ trong `__pycache__` vẫn được dùng => chạy với `PYTHONDONTWRITEBYTECODE=1` hoặc xoá `__pycache__`.

## Phase 2 - Metrics + CLI `metrics`

- `src/metrics/evaluate.py`, `src/metrics/report.py` theo mục 3-4, 6.
- `cli.py`: tách `run_score`, thêm lệnh `metrics` theo mục 2; docstring đầu file thêm lệnh. In ra màn hình: precision / recall / FPR + đường dẫn report.
- Test hệ thống `tests/test_system_metrics.py` (dữ liệu dựng trong test): đếm TP/FP/FN/TN trên ví dụ nhỏ biết trước đáp án; FP dính 2 rule đếm cho cả 2 (mục 4); bảng ngưỡng đúng ranh giới `>=`; ground truth thiếu / thừa claim_id => lỗi.
- Chạy `metrics` trên data thật => sinh `output/metrics_report.md` (commit file này).
- Spec giao cho `coder`; sau đó `reviewer`.

**Xong (2026-10-25).** Review 3 lượt (2 vòng sửa). Vòng 1:
- Ground truth kiểm thêm pattern: fraud phải thuộc `ALL_RULES`, legit phải rỗng. Trước đó pattern gõ sai làm report vẫn ghi "Every pattern is fully caught".
- Fixture FPR có TP != TN, vì mẫu số sai FP+TP trước đó vẫn pass.
- Thêm test biên `>= 70`, test sai số cột, test `claim_id` trùng.
- Report: số có dấu phân cách; bỏ dòng tổng FP khỏi bảng; câu nhận xét suy từ số; câu "upper bound" cho dữ liệu tổng hợp; "seed unknown".
- Claim dính thêm rule tách Expected (phantom day) / Unexpected.

Vòng 2:
- Test đủ 4 chiều của điều kiện "rule thừa duy nhất là `phantom_billing`".
- `load_phantom_day_claims` trả `None` khi số claim khớp khác `claims` trong summary (trước đó trả tập rỗng, lặng lẽ đẩy 6 claim sang Unexpected).

Main thread sửa nốt câu số ít "its own pattern". 149 test pass, số trên data thật khớp "Số đo sơ bộ". Không làm, có lý do:
- Chuyển `GROUND_TRUTH_COLUMNS` sang module chung: phải sửa generator, metrics import thẳng từ `generator.dataset` là đủ.
- Câu "see Limitations in README.md" trỏ tới mục chưa có: giao cho #04, đã ghi Notes.

## Phase 3 - Test tích hợp + số đo thật

- `tests/test_integration_dataset.py`, đọc `data/` đã commit:
  - Mỗi claim fraud có flag của pattern mình; rule thừa chỉ được là ngoại lệ mục 5.
  - Recall >= 70%, FPR <= 20% (mục tiêu của đề).
  - Pipeline load -> score trên 2,000 claim < 30 giây.
- `docs/experiences/dataset-generation-pitfalls.md` (đã là tiếng Anh): dòng Status đổi thành "re-checked by the engine on 2026-10-25", thêm "engine: ..." vào mục 1, 3, 8, 9 (khớp / lệch so với script nháp).
- Main thread tự làm (test ngắn + docs); `reviewer` cho file test.

**Xong (2026-10-25).** Main thread viết test + docs, review 1 lượt. 4 test tích hợp ban đầu không rỗng: mutation rule trả `{}`, rapid flag mọi claim, rapid 30 ngày, SD 1, band 30,000, phantom 31, `MAX_SECONDS` nhỏ đều bị bắt. Sửa theo 3 lỗi Low:
- Thêm test `check_same_claims`, vì trước đó claim bị rơi chỉ lộ ở test thời gian (`1999 == 2000`).
- Status của pitfalls doc nói rõ engine chỉ đo lại mục 1, 2, 3, 8, 9.
- "Guarded by" chỉ gắn với điều test thật sự kiểm.

154 test pass.

## Verify

- `uv run pytest`: 111 test cũ + 19 test business + test metrics + test tích hợp đều pass.
- `uv run python src/cli.py metrics` ra đúng các số ở mục "Số đo sơ bộ"; lệch => dừng tìm nguyên nhân.
- Mutation thủ công (không commit): đổi ngưỡng phantom `> 30` thành `>= 30` => TC11 fail; đổi cửa sổ rapid 7 -> 8 => TC4 fail; bỏ ngoại lệ phantom day trong test tích hợp => fail và message nêu đúng 6 claim.
- Đọc `metrics_report.md` bằng mắt: đủ 4 phần + thời gian, người không đọc code vẫn hiểu.

## Ghi chú cho #04

Đã ghi vào mục Notes của ticket #04 (2026-10-25).

- Recall 100% / FPR 2.6% là "quá đẹp" vì cùng 1 người viết rule và sinh dữ liệu theo đúng định nghĩa rule. Writeup cần nói rõ hạn chế này (dữ liệu thật sẽ thấp hơn) thay vì khoe số.
- Ngưỡng >= 70 chỉ còn recall 18%: nếu người thẩm định chỉ xem claim điểm cao sẽ bỏ sót phần lớn fraud => lý do chọn `> 0` làm metric chính.

## Quy trình

- Áp dụng `/pyfriend-claco-bunhy` khi viết code.
- Review theo bảng Agent workflow ở `AGENTS.md` gốc; trước commit chạy `/pjdoc-mgmt-claco-bunhy pre-commit`.
