# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | Envelope encryption cho cột nhạy cảm bằng AES-256-GCM; TLS 1.3 tại API gateway/reverse proxy | ✅ Done | Infra Team |
| Audit logging | Ghi log truy cập API theo user/role/token fingerprint; lưu immutable audit logs trên storage nội bộ tại VN; cảnh báo khi truy cập raw PII trái phép | ✅ Done | Platform Team |
| Breach detection | Prometheus + Grafana + alert rules cho access anomaly, failed auth spike, data export volume và integrity errors | ✅ Done | Security Team |

## F. Technical Solutions
Audit logging:
- Log mọi request tới `raw`, `anonymized`, `aggregated` API với `username`, `role`, `resource`, `action`, timestamp và kết quả `allow/deny`.
- Đẩy log sang hệ thống tập trung tại VN, bật retention tối thiểu 180 ngày và chống sửa đổi bằng bucket/object lock hoặc WORM storage.
- Tạo dashboard theo dõi truy cập PII và rule cảnh báo khi cùng một token truy cập raw data bất thường.

Breach detection:
- Dùng Prometheus scrape API metrics, auth failure counts, delete attempts và file integrity metrics.
- Cấu hình Grafana alert gửi email/Slack/PagerDuty khi phát hiện spike truy cập thất bại, export data tăng đột biến hoặc thao tác delete ngoài khung giờ.
- Kết hợp Bandit, pip-audit, git-secrets và TruffleHog trong SDLC để giảm nguy cơ rò rỉ trước khi triển khai.
