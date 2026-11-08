# Hệ thống điều khiển xe rover qua mạng Wi-Fi dùng PX4

## Mục tiêu dự án
Xây dựng ứng dụng điều khiển và giám sát xe rover qua mạng Wi-Fi.
Xe chạy firmware PX4 và giao tiếp với ứng dụng bằng giao thức MAVLink.
Trong giai đoạn phát triển, xe được mô phỏng bằng PX4 SITL + Gazebo (xe mẫu `gz_r1_rover`).

## Thành viên thực hiện
- Vũ Duy Dương
- Trương Nhật Hoàng
- Đinh Trần Thảo Phương

## Giảng viên hướng dẫn
TS. Đào Duy Tuấn

## Phương pháp
Agile (Scrum kết hợp các thực hành XP):
- Làm theo từng sprint ngắn. Mỗi sprint hoàn thành một hoặc vài user story.
- Phần nào test tự động được thì viết test trước rồi mới viết code.
- Nhóm tự chạy kiểm thử chấp nhận với xe mô phỏng.
- Story mới chỉ được thêm vào product backlog sau sprint review và retrospective.

## Quy trình làm việc theo Agile

Một vòng lặp gồm các bước sau. Hết một vòng thì quay lại bước 1 cho sprint tiếp theo.

    [1] Product backlog
          |
    [2] Sprint planning
          |
    [3] Daily Scrum  <-- thực hiện các task
          |
    [4] Kiểm thử chấp nhận
          |
    [5] Sprint review
          |
    [6] Sprint retrospective
          |
          +--> quay lại [1]

### 1. Product backlog – chọn việc cần làm
- Khách hàng (Product Owner) đưa yêu cầu. Mỗi yêu cầu được viết thành user story theo mẫu:
  "Là <vai trò>, tôi có thể <hành động> để <mục đích>."
- Các story được sắp xếp theo độ ưu tiên.
- File: `docs/agile/product-backlog.txt`

### 2. Sprint planning – lên kế hoạch cho sprint
- Chọn story ưu tiên cao nhất cho sprint.
- Viết tiêu chí chấp nhận: khách hàng kiểm tra bằng cách nào, kết quả thế nào thì đạt.
- Chia story thành các task nhỏ. Với mỗi task, ghi rõ phần nào test tự động, phần nào kiểm bằng tay.
- Đặt mục tiêu sprint, gói trong một câu.
- File: `docs/agile/US-xx.txt`, `docs/agile/sprint-xx.txt`

### 3. Thực hiện sprint – làm từng task
Với mỗi task, làm theo thứ tự:
1. Chuyển trạng thái task sang `DOING`.
2. Viết test trước (nếu test tự động được). Chạy `pytest`: test mới phải **fail**.
3. Viết code. Chạy lại `pytest`: toàn bộ test phải **pass**.
4. Commit theo dạng `US-xx/Tx: <nội dung>`.
5. Kiểm tra lại Definition of Done, rồi chuyển task sang `DONE`.
6. Nếu gặp lỗi chưa sửa được, ghi vào `docs/agile/bug-log.txt`.

Trong suốt sprint, nhóm họp ngắn hằng ngày (daily stand-up). Mỗi người trả lời ba câu:
đã làm gì, sẽ làm gì, đang vướng gì.

### 4. Kiểm thử chấp nhận
- Khi tất cả task đã `DONE`, nhóm tự chạy các tiêu chí chấp nhận (AC) với xe mô phỏng.
- Ghi kết quả Đạt/Không đạt cho từng AC vào `docs/agile/sprint-xx.txt`.

### 5. Sprint review – đánh giá sản phẩm
- Trình diễn phần mềm đã làm được trong sprint.
- Kết luận story có đạt hay không, và ghi lại phản hồi của khách hàng.
- Story đạt thì chuyển trạng thái sang `XONG` trong product backlog.

### 6. Sprint retrospective – đánh giá cách làm
- Điều gì làm tốt, điều gì cần cải thiện, hành động cụ thể cho sprint sau.
- Cùng thống nhất story tiếp theo và thêm vào product backlog.
- File: `docs/agile/sprint-xx.txt` (phần Retrospective)

### Trạng thái dùng trong tài liệu
| Đối tượng | Các trạng thái |
|---|---|
| Story | `MOI` → `SAN_SANG` → `DANG_LAM` → `XONG` |
| Task  | `TODO` → `DOING` → `DONE` |
| Lỗi   | `MO` → `DANG_SUA` → `DA_SUA` |

## Tài liệu Agile
| File | Nội dung |
|---|---|
| `docs/agile/product-backlog.txt` | Danh sách user story theo thứ tự ưu tiên và trạng thái |
| `docs/agile/US-xx.txt` | Chi tiết từng story: tiêu chí chấp nhận, task, yêu cầu test |
| `docs/agile/sprint-xx.txt` | Mục tiêu sprint, sprint backlog, kết quả review và retrospective |
| `docs/agile/definition-of-done.txt` | Điều kiện để task và story được tính là xong |
| `docs/agile/bug-log.txt` | Nhật ký lỗi |

## Môi trường
- Ubuntu, VS Code
- PX4-Autopilot (PX4 SITL + Gazebo)
- Python 3

## Cài đặt (lần đầu sau khi clone)

    git clone https://github.com/wenxizhabg/rover-control-by-PX4
    cd rover-control-by-PX4
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt


## Chạy test

    pytest          # tóm tắt: mỗi dấu . là một test pass, F là fail
    pytest -v       # hiện tên từng test và PASSED/FAILED

Kết quả đạt: dòng cuối báo toàn bộ `passed`, không có `failed`.


## Bật và tắt mô phỏng

### Bật
Mở một terminal riêng cho mô phỏng (giữ nguyên terminal này trong suốt quá trình làm việc):

    cd ~/PX4-Autopilot
    make px4_sitl gz_r1_rover

- Lần đầu chạy sẽ biên dịch PX4, mất vài phút. Những lần sau chạy nhanh hơn.
- Bật xong khi: cửa sổ Gazebo hiện xe `r1_rover` và terminal hiện dấu nhắc `pxh>`.

### Kiểm tra PX4 đang gửi MAVLink cho ứng dụng
Tại dấu nhắc `pxh>`, gõ:

    mavlink status

Trong danh sách instance phải có một dòng `partner IP: 127.0.0.1` với `remote port: 14540`.
Đây là cổng mà ứng dụng của nhóm sẽ nghe. Cổng 14550 dành cho QGroundControl.

### Tắt
Tại dấu nhắc `pxh>`, gõ `shutdown`, hoặc nhấn `Ctrl+C` trong terminal mô phỏng.

Nếu lần bật sau báo lỗi do Gazebo cũ vẫn còn chạy:

    pkill -9 -f "gz sim"
    
## Trạng thái hiện tại
Sprint 1 – US-01: Bật mô phỏng Gazebo và kết nối đến xe.
