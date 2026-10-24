# Plan 01 - A: Sinh dataset

> **Ticket:** #01 - trạng thái và mục tiêu nằm ở ticket; file này chỉ chứa chi tiết thực thi.

Nguồn business: `docs/business-rule/fraud-injection.md`, `catalog.md`, `icd-10.md`, `diagnosis-procedure-mismatch.md`, `weekday-only-providers.md`, `upcoding.md`, `amount-clustering.md`, `bundling.md`, `duplicate-and-rapid-resubmission.md`. Định dạng: `docs/decisions/dataset-format.md`. Bẫy: `docs/experiences/dataset-generation-pitfalls.md`.

## Đã chốt trước khi code (2026-10-24)

Đường dẫn trong plan tính từ `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/`. Đã ghi vào business doc: mục 1 -> `diagnosis-procedure-mismatch.md`, mục 2-3 -> `fraud-injection.md`, `upcoding.md`.

1. **Lỗi business doc: claim unbundled của B-1001 và B-1002 sẽ dính thêm mismatch.** `detection-rules.md` ghi "các mã thành phần đều là cặp hợp lệ với diagnosis của gói", nhưng đối chiếu bảng cặp hợp lệ thì sai:
   - B-1001 = P-1001 + P-1002 + **P-1003**; diagnosis hợp lệ của gói là J06.9, I10, nhưng P-1003 không hợp lệ với J06.9 hay I10.
   - B-1002 = P-1001 + **P-1002** + P-1006; diagnosis hợp lệ của gói là E11.9, nhưng P-1002 không hợp lệ với E11.9.
   - B-3101, B-3102, B-4101 không có vấn đề.
   - Đã chốt: thêm 3 cặp hợp lệ `J06.9 - P-1003`, `I10 - P-1003`, `E11.9 - P-1002` (hợp lý về y khoa: khám tổng quát có xét nghiệm nước tiểu, theo dõi đái tháo đường có công thức máu). Tổng thành 35 cặp. Hệ quả: P-1003 có thêm diagnosis hợp lệ, không ảnh hưởng clustering.
2. **Amount của claim fraud ngoài pattern amount:** hệ số dao động bị kẹp trong [0.85, 1.15] (khoảng +-1 SD), để claim duplicate / rapid / phantom / weekend / mismatch / unbundling không vô tình dính upcoding hay clustering. Claim hợp lệ vẫn dùng log-normal không kẹp (giữ FP tự nhiên có chủ đích).
3. **Làm tròn amount:** mọi claim (hợp lệ và fraud) làm tròn tới 100 VNĐ, giống bảng giá thật (27,400 / 46,200 trong `catalog.md`). Claim clustering lấy ngẫu nhiên trong 47,500-49,999. Sửa 2026-10-24: bản trước làm tròn claim hợp lệ tới 1,000 và clustering tới 100, khiến mọi amount không chia hết cho 1,000 là fraud clustering (lộ nhãn qua định dạng).

## Phase 1 - Khung project và config

- `pyproject.toml` (uv): Python >= 3.12, dev dependency `pytest`; `[tool.pytest.ini_options] pythonpath = ["src"]`.
- `src/config/catalog.json`: procedure (mã, tên EN, claim_type, giá chuẩn, surgical), bundle (mã, tên EN, thành phần, giá, surgical), diagnosis (mã, tên EN, claim_type), cặp hợp lệ. Nguồn duy nhất, generator và engine cùng đọc.
- `src/catalog.py`: load và kiểm `catalog.json` (mã trong cặp hợp lệ phải tồn tại, thành phần bundle phải tồn tại). Dùng chung cho A và B.
- Tên provider viết không dấu (vd `Benh vien Da khoa An Phuc`), không chứa `,`: tránh lỗi NFC/NFD và lỗi CSV.

**Tiến độ (2026-10-24): xong.**
- Bundle có thêm trường `claim_type` (plan ban đầu không ghi), để Phase 5 kiểm "claim_type khớp mã" cả với mã bundle; `catalog.py` kiểm nó trùng với claim_type của mọi thành phần.
- `catalog.py` kiểm thêm ràng buộc "diagnosis hợp lệ của bundle phải hợp lệ với mọi thành phần" (mục 1 ở trên); bỏ 2 cặp `J06.9 - P-1003`, `E11.9 - P-1002` thì validate báo đúng 2 lỗi.
- Bổ sung (2026-10-24, xong): `src/config/providers.json` gồm 50 provider (`id`, `name`, `type`: HOSPITAL / CLINIC / DENTAL), ID cố định nhưng xen kẽ loại (không để `PRV-001..020` toàn bệnh viện) để ID không lộ loại provider. Tên không dấu, không chứa `,`, không trùng. Chỉ generator đọc; danh sách weekday-only **không** ghi ở đây (generator chọn theo seed, ghi vào `generation_summary.json`), vì engine phải tự phát hiện từ dữ liệu. Thay cho cách "xáo rồi gán ID theo seed" ở Phase 2.
- Đã chốt: 2 cặp hợp lệ khác claim_type (`K80.2 - P-1005`, `J18.9 - P-1004`, diagnosis INPATIENT + procedure OUTPATIENT) giữ nguyên. claim_type của diagnosis chỉ để tham khảo; claim_type của claim lấy theo mã procedure / bundle. Phase 5 không kiểm claim_type của diagnosis.

## Phase 2 - Provider và claim hợp lệ (1,800 claim)

- **Provider (50):** đọc từ `src/config/providers.json`: 20 bệnh viện (OUTPATIENT + INPATIENT), 20 phòng khám (OUTPATIENT), 10 nha khoa (DENTAL). 10 bệnh viện weekday-only chọn theo seed.
- **Member:** `MEM-0001`..`MEM-0500`, chọn đều (không chia trước; kỳ vọng ~491 member xuất hiện, Phase 5 kiểm >= 480).
- **Hạn mức theo mã:** bảng số claim hợp lệ cố định cho từng mã trong 21 mã (`LEGIT_CLAIMS_PER_CODE` trong `src/generator/legit.py`, tổng 1,800): mỗi mã >= 30, ngoại trú nhiều nhất, 18 mã ngoài P-1003 có >= 60 (đủ chỗ rải 27 claim upcoded, tối đa 2/mã). Dùng số cố định thay vì chia theo trọng số ngẫu nhiên để mã sát 60 không bị rơi xuống dưới 60 tùy seed.
- **Diagnosis:** chọn ngẫu nhiên trong các diagnosis hợp lệ của mã.
- **Provider cho claim:** đúng loại theo claim_type. Mỗi bệnh viện weekday-only nhận ngẫu nhiên 62-70 claim (OUTPATIENT / INPATIENT) và không nhận thêm; phần còn lại chia ngẫu nhiên cho provider khác. Lý do không cho bốc thêm: bản đầu cho bốc thêm thì 10 bệnh viện này có 84-95 claim so với 15-27 của bệnh viện thường, tức 10 bệnh viện lớn nhất luôn là nhóm weekday-only (dấu vết dễ thấy, ngược thực tế).
- **Ngày:** bệnh viện weekday-only chỉ thứ Hai - thứ Sáu; provider khác chọn đều trong 2024. `is_weekend` suy ra từ ngày.
- **Amount:** giá chuẩn x `exp(N(0, 0.15))`, làm tròn 100.
- **Không tạo duplicate ngẫu nhiên:** nếu unique key `(member, provider, date, diagnosis)` đã tồn tại thì chọn lại ngày.

**Tiến độ (2026-10-24): xong** (`src/generator/models.py`, `src/generator/legit.py`, thêm `Catalog.diagnoses_for`). Số đo sơ bộ trên 1,800 claim hợp lệ, seed 2024 (chưa có fraud, số chính thức đo lại sau Phase 5):
- 483 member, 50 provider; weekday-only 63-69 claim, bệnh viện thường 31-45, phòng khám 10-24, nha khoa 34-59; provider-day lớn nhất 3; 0 duplicate.
- FP tự nhiên: upcoding 57 claim (ước lượng cũ 40-45; log-normal lệch phải nên ~3.2% vượt mean + 2 SD), rapid 32 claim (ước lượng cũ 10-20), P-1003 trong dải clustering 6/90.

## Phase 3 - Chèn 200 claim fraud

| Pattern | Cách sinh | Ghi chú |
|---|---|---|
| Duplicate 30 | 15 cặp cùng member + provider + date + diagnosis, procedure hợp lệ | Provider weekday-only thì ngày thường |
| Rapid 30 | 15 cặp cùng member + diagnosis, cách 1-7 ngày, provider có thể khác | |
| Upcoding 30 | Giá chuẩn x U(1.6, 2.5), claim 1 mã | 27 claim rải trên các mã có >= 60 claim, tối đa 2 claim/mã, không dùng P-1003; 3 claim nằm trong ngày phantom |
| Unbundling 25 | 5 bundle x 5 claim; `procedure_codes` = đủ thành phần; amount = tổng giá lẻ x hệ số kẹp | Diagnosis hợp lệ của gói (35 cặp hợp lệ, mục 1) |
| Phantom 25 | 1 bệnh viện thường, 1 ngày thường mà provider chưa có claim nào; 25 claim ngoại trú hợp lệ | Cùng ngày có thêm 3 upcoding + 3 mismatch => tổng 31 |
| Weekend 20 | 10 bệnh viện weekday-only x 2 claim; mã surgical (P-3001, P-3002, P-3003, B-3101, B-3102) với diagnosis hợp lệ; thứ Bảy / Chủ nhật | |
| Mismatch 20 | 17 claim + 3 claim trong ngày phantom; procedure cùng claim_type nhưng ngoài danh sách hợp lệ của diagnosis, không dùng mã bundle | Amount theo giá chuẩn x hệ số kẹp |
| Clustering 20 | P-1003, diagnosis N39.0, amount 47,500-49,999 | |

- Lý do rải upcoding trên mã >= 60 claim, tối đa 2 claim/mã: với mã chỉ 30 claim, 2 claim upcoded có thể đẩy SD lên khoảng 0.3 x mean, ngưỡng thành khoảng 1.65 x mean, bỏ sót claim upcoded 1.6x (masking).

**Tiến độ (2026-10-24): xong** (`src/generator/fraud.py`, `src/rule_names.py`).
- Tên pattern = tên rule, snake_case theo tiêu đề rule của đề, đặt ở `src/rule_names.py` để #02 dùng chung: `duplicate_claim`, `rapid_resubmission`, `upcoding`, `unbundling`, `phantom_billing`, `weekend_anomaly`, `diagnosis_procedure_mismatch`, `amount_clustering`.
- Mỗi claim fraud được đặt sao cho không vô tình dính rule khác: không tạo unique key duplicate mới, không có claim cùng member + diagnosis trong 7 ngày, bệnh viện weekday-only chỉ nhận ngày thường (trừ weekend), amount kẹp +-15%. Phantom sinh cuối cùng để không claim nào rơi thêm vào provider-day đó.
- Clustering lấy amount `47,500..49,900` bước 100 (cùng cách làm tròn với mọi claim).
- Kiểm thô (seed 2024, chưa phải engine): đúng số theo pattern; 1 provider-day 31 claim (PRV-006, 2024-11-05, thứ Ba); 15 nhóm duplicate; weekday-only 67-78 claim, claim cuối tuần của nhóm này chỉ là 20 claim weekend; 30/30 upcoded vượt mean + 2 SD, không claim fraud khác vượt, 23 claim hợp lệ vượt (giảm từ 57 khi chưa có fraud vì claim upcoded kéo SD lên); dải clustering: 20 fraud + 2 hợp lệ; mismatch chỉ gồm 20 claim mismatch; claim nhiều mã chỉ là 25 unbundling; cặp rapid: 30 fraud + 20 hợp lệ, không pattern khác; 488 member; mã ít nhất 44 claim 1 mã.

## Phase 4 - Gán ID, ghi file

- Gộp claim hợp lệ + fraud, sắp theo `claim_date`, thứ tự phụ ngẫu nhiên theo seed, rồi gán `CLM-00001`..`CLM-02000` (tránh lộ nhãn qua ID).
- Ghi `data/claims.csv`, `data/ground_truth.csv` theo `dataset-format.md`.
- Ghi `data/generation_summary.json`: seed, danh sách provider weekday-only, provider-day phantom, số claim theo pattern, số claim theo mã.
- CLI: `uv run python src/cli.py generate [--seed 2024]`.

## Phase 5 - Kiểm cấu trúc (chạy cuối lệnh generate, lỗi thì dừng)

- 2,000 claim, `claim_id` duy nhất, đúng 10 cột; 200 fraud, đúng số theo pattern.
- Số member khác nhau trong 480-500, đúng 50 provider, mọi ngày trong 2024, `is_weekend` khớp ngày, claim_type khớp mã.
- Mỗi `provider_id` luôn đi với đúng 1 `provider_name` và ngược lại.
- `procedure_codes`: mọi mã có trong catalog; claim không phải unbundling có đúng 1 mã; claim unbundling có đúng đủ thành phần của 1 bundle.
- `submitted_amount`: số nguyên dương, chia hết cho 100; claim clustering nằm trong 47,500-49,999.
- Mỗi mã >= 30 claim 1 mã.
- Mỗi bệnh viện weekday-only >= 60 claim, không có claim hợp lệ cuối tuần.
- Nhóm theo unique key duplicate: đúng 15 nhóm có 2 claim, không nhóm nào khác > 1.
- Chỉ đúng 1 provider-day > 30 claim, và nó có đúng 31 claim.
- In bảng tóm tắt ra màn hình.

Không chép logic rule vào đây; kiểm chéo rule với nhãn thuộc #03.

## Verify

- Chạy `generate` 2 lần cùng seed => 2 file giống hệt (so sha256).
- Mở `claims.csv`, đọc mắt 20 dòng: amount hợp lý, tên provider, `procedure_codes` dạng `P-1001|P-1002`.
- Kiểm vị trí `claim_id` của claim fraud rải đều (không dồn cuối).
- Đếm nhanh cặp cùng member + diagnosis cách <= 7 ngày trong claim hợp lệ (ước FP tự nhiên của rapid) và ghi vào `dataset-generation-pitfalls.md`.
- Áp dụng `/pyfriend-claco-bunhy` khi viết code; review diff trước commit; chạy `/pjdoc-mgmt-claco-bunhy pre-commit`.
