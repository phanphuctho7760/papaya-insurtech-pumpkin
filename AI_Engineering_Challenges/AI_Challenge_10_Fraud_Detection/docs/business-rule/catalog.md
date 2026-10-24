# Catalog: procedures, bundles, standard prices

Reference data shared by the generator (part A) and the engine (part B). Terms (procedure, surgical, bundle, standard price, variation): see `glossary.md`.

## Role of the price list

- This is a hiring test: the price list is a **simulated example**. In practice the insurer / TPA already has an official price list.
- What the price list must achieve here: **plausible** prices that **do not break the rules** (e.g. legitimate claims do not exceed the upcoding threshold by themselves, clustering claims do not trip upcoding). Accuracy against the market is secondary.

## Conventions

- Currency: **VND**, keeping the brief's numbers as they are (auto-approval threshold 50,000 VND).
- Price level: **private hospitals / clinics** in Vietnam (private health insurance is mostly used at private facilities).
- Diagnosis codes: real ICD-10, see `icd-10.md`. Procedure and bundle codes: made up.
- A legitimate claim has **exactly 1 code** in `procedure_codes` (an individual procedure code or a bundle code). Claims with several codes only appear as unbundling fraud.
- Legitimate claim amount = standard price x a random log-normal factor, variation about 15%.

## Procedures

| Code | Procedure | claim_type | Standard price (VND) | Surgical |
|---|---|---|---|---|
| P-1001 | General consultation | OUTPATIENT | 200,000 | |
| P-1002 | Complete blood count | OUTPATIENT | 100,000 | |
| P-1003 | Urinalysis | OUTPATIENT | 40,000 | |
| P-1004 | Chest X-ray | OUTPATIENT | 150,000 | |
| P-1005 | Abdominal ultrasound | OUTPATIENT | 250,000 | |
| P-1006 | HbA1c test | OUTPATIENT | 150,000 | |
| P-2001 | Inpatient pneumonia treatment | INPATIENT | 10,000,000 | |
| P-2002 | Normal vaginal delivery | INPATIENT | 30,000,000 | |
| P-3001 | Laparoscopic appendectomy | INPATIENT | 18,000,000 | x |
| P-3002 | Laparoscopic cholecystectomy | INPATIENT | 25,000,000 | x |
| P-3003 | Open reduction internal fixation (bone surgery) | INPATIENT | 22,000,000 | x |
| P-3010 | General anesthesia | INPATIENT | 3,000,000 | |
| P-4001 | Dental examination | DENTAL | 100,000 | |
| P-4002 | Dental X-ray | DENTAL | 80,000 | |
| P-4003 | Dental filling | DENTAL | 400,000 | |
| P-4004 | Root canal treatment | DENTAL | 2,000,000 | |

## Bundles (5)

A bundle costs about 90% of the sum of its components. Rule details: `bundling.md`.

| Bundle code | Name | Components | Sum of components | Bundle price | Surgical |
|---|---|---|---|---|---|
| B-1001 | General check-up package | P-1001 + P-1002 + P-1003 | 340,000 | 305,000 | |
| B-1002 | Diabetes check-up package | P-1001 + P-1002 + P-1006 | 450,000 | 405,000 | |
| B-3101 | Appendectomy package | P-3001 + P-3010 | 21,000,000 | 19,000,000 | x |
| B-3102 | Cholecystectomy package | P-3002 + P-3010 | 28,000,000 | 25,500,000 | x |
| B-4101 | Root canal package | P-4002 + P-4004 | 2,080,000 | 1,900,000 | |

## English names (used in evidence)

| Code | English name |
|---|---|
| P-1001 | General consultation |
| P-1002 | Complete blood count |
| P-1003 | Urinalysis |
| P-1004 | Chest X-ray |
| P-1005 | Abdominal ultrasound |
| P-1006 | HbA1c test |
| P-2001 | Inpatient pneumonia treatment |
| P-2002 | Normal vaginal delivery |
| P-3001 | Laparoscopic appendectomy |
| P-3002 | Laparoscopic cholecystectomy |
| P-3003 | Open reduction internal fixation |
| P-3010 | General anesthesia |
| P-4001 | Dental examination |
| P-4002 | Dental X-ray |
| P-4003 | Dental filling |
| P-4004 | Root canal treatment |
| B-1001 | General check-up package |
| B-1002 | Diabetes check-up package |
| B-3101 | Appendectomy package |
| B-3102 | Cholecystectomy package |
| B-4101 | Root canal package |

## Providers

- 50 providers of 3 types: hospitals (inpatient, surgery), clinics (outpatient), dental clinics (dental).
- 10 weekday-only hospitals: see `weekday-only-providers.md`.

## Price sources

The price list is simulated. Most standard prices are estimates from general knowledge; the items below were checked against sources (researched 2026-10-24; many sources are old price lists or aggregator blogs):

| Code | Sources found | Notes |
|---|---|---|
| P-1002 | Public 46,200-70,000; private 98,000 (DIAG) | Set to 100,000 to match private prices |
| P-1003 | Public 27,400-28,600 (with public health insurance), 48,000 (without) | No private source yet; 48,000 falls right in the clustering band |
| P-1006 | Public 101,000-143,000; private 120,000-150,000 | Matches |
| P-2002 | Private 27-45 million (Vinmec, Tam Anh) | Set to 30 million, private price level |
| P-3001 | Private 8-30 million (Long Chau) | Matches |
| P-4003 | 150,000-500,000 | Matches |

Source links:
- BV Phụ sản Hải Phòng: https://benhvienphusanhaiphong.vn/Images/news/Bảng%20giá%20viện%20phí%20khám%20chữa%20bệnh.pdf
- NQ 45/2024 Hà Nội: https://storage-vnportal.vnpt.vn/gov-hni/6249/VanBanCongBao/2025/3/28/NQPQ-45-2025-23_signed.pdf
- Medpro (blood test): https://medpro.vn/tin-tuc/xet-nghiem-mau-bao-nhieu-tien
- Pharmacity (HbA1c): https://www.pharmacity.vn/xet-nghiem-hba1c-gia-bao-nhieu.htm
- Vinmec normal delivery (via Medpro): https://medpro.vn/tin-tuc/chi-phi-sinh-o-vinmec-bao-nhieu
- Tâm Anh delivery package: https://tamanhhospital.vn/sinh-con-tron-goi/
- Long Châu (appendectomy): https://nhathuoclongchau.com.vn/bai-viet/thac-mac-chi-phi-mo-ruot-thua-bao-nhieu-tien-69480.html
- Medpro (dental filling): https://medpro.vn/tin-tuc/gia-tram-rang-bao-nhieu-tien
