# Bundling và Unbundling (tách gói)

## Thuật ngữ

- Bundle (gói): nhóm procedure luôn đi cùng nhau, tính bằng 1 mã gói, rẻ hơn tổng giá lẻ.
- Unbundling: khai từng procedure lẻ thay vì mã gói để thu nhiều tiền hơn. Ví dụ khai riêng mổ ruột thừa (P-3001) + gây mê (P-3010) thay vì gói B-3101.

## Nguồn trong đề

- Dataset: "25 unbundled claims (individual procedures that should be a single bundled code)".
- Rule 4: "multiple individual procedures when a bundled code exists (provide a mapping of at least 5 bundles)".

## Thế nào là "chuẩn"

- 5 bundle và thành phần: xem `catalog.md`, mục Bundle.
- Claim hợp lệ có thành phần thuộc một gói thì dùng mã gói (1 mã duy nhất).

## Rule

- Flag khi `procedure_codes` của claim chứa **đủ tất cả** thành phần của một bundle.
- Claim chỉ chứa một phần thành phần: không flag.

## Quy tắc sinh fraud

- Claim unbundled: `procedure_codes` = toàn bộ thành phần của một gói; amount = tổng giá lẻ x hệ số dao động.
- Diagnosis phải là chẩn đoán hợp lệ cho gói đó (để không dính thêm mismatch).
