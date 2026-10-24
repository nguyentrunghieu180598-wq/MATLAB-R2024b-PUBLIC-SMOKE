# JTE053 — diagnostic 20 giây với khóa Work Cloud mới (chưa chạy)
1. Work phải xác nhận vẫn truy cập được private RSA key JTE052 trong đúng Cloud runner hiện tại, và test fingerprint public 912e8393... trùng mới tiếp tục. Không đưa private bytes vào prompt/log/repo/Drive khi chưa có ủy quyền.
2. Chỉ khi Work có thể giám sát và tải output ngay trong cùng runtime, tạo file `jte053/TRIGGER_20S.txt` trên branch `chat/jte053-cloud-20s-transport`. Hành động push này mới kích hoạt workflow; tạo workflow/mã trước đó **không kích hoạt mô phỏng**.
3. Theo dõi GitHub Actions, lấy encrypted ZIP artifact qua binary download API, kiểm digest và envelope recipient, xác thực RSA-OAEP/AES-GCM. Đọc dữ liệu REAL 20s từ MAT riêng của Work, xác minh Time/Data 312 kênh, zero-bias, signal names; không công bố số nhiệt ra public logs.
4. Lưu authenticated plaintext data hoặc chỉ biên nhận/report phù hợp vào Drive owner-only đã kiểm tra write+readback; không lưu private RSA key qua Drive sau approval denial. Nếu cloud session mất khóa, thử nghiệm 20s có thể được lặp lại với recipient mới sau khi được phép; chưa chạy 2400s.
5. Work trả `JTE053_DIAGNOSTIC_20S_REPORT.md` với run ID, head SHA, sha256 ciphertext/plaintext, GCM-authentic=yes/no, 312 channels yes/no, exact failure, cloud access, private readback. Chat sẽ nghiệm thu riêng G5 sau đó.

**Known limitations:** Source builder is pinned and logs only jteUcore (pre-filter). This 20s pilot is not G5, not pump energy, not proof of a validated Porsche Taycan model. Vendor source remains unchanged. Stop on failure and do not run 2400s.
