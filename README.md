# Pet data cho EmojiBattery

Folder này nằm ngoài Android project, không được đóng gói vào APK.

## Cấu trúc app hiện tại

App đang chọn Constants.PET_DATA_SOURCE = EMOJI_REMOTE_CONFIG.
Remote Config hỗ trợ data_pet (gifUrls), data_pet_moving_v3 (các action có frames/urls, hoặc walkStatuses theo mức pin 20/50/80/100), pet_type (type/name).
Mỗi pet mới có id, name, type, thumbnail, is_lock và các action walk/climb/top/drag/fall/drop/sit/run khi đủ frame.
App chuyển thumbnail thành image_url, dùng type làm category và tải ảnh theo HTTPS. URL tuyệt đối cho phép dùng repo mới mà không đổi code app.

## Nội dung folder

- source.csv: bản xuất nguyên tab Tất cả.
- archives/: gói nguồn của từng dòng.
- assets/: ảnh/XML đã giải nén; tên file được đánh số để URL ổn định, an toàn.
- full-animation/: các gói ở cột Bản full animation, giữ riêng để không trộn biến thể.
- manifest.json: đối chiếu tên gốc, file xuất, SHA256, nguồn và trạng thái từng dòng.
- publish/: JSON dùng cho app, chỉ bao gồm pet có đủ chuỗi Walk.
- reports/summary.json: kết quả tải và các pet cần map thủ công.
- remote-config-values.json: các key/value cần nhập vào Firebase Console.

## Sau khi upload GitHub

Upload assets/ và publish/ vào cùng gốc repo public. Có thể giữ archives/, full-animation/ và reports/ ở máy; app không cần các folder đó.

Tạo lại JSON với đúng URL repo (thay YOUR_ACCOUNT/YOUR_REPO/BRANCH):

    python build_catalog.py --base-url https://raw.githubusercontent.com/YOUR_ACCOUNT/YOUR_REPO/BRANCH

Upload lại publish/ sau khi tạo JSON. Bản có OWNER/REPO chỉ là template, chưa dùng được trong app.

Firebase Remote Config:

- data_pet_moving_v3 = URL HTTPS raw trỏ đến publish/data_pet_moving_v3.json
- pet_type = URL HTTPS raw trỏ đến publish/pet_type.json
- data_pet = [] (để bỏ danh sách idle cũ, tránh trộn nguồn)

Không nhập nguyên remote-config-values.json thành Firebase template; đây chỉ là bảng key/value.
Không dùng emoji_battery_content_url cho file mảng này: key đó yêu cầu object catalog đầy đủ có schema_version/themes/emojis.
App có cache cũ và fetch interval 1 giờ, nên dữ liệu có thể chưa đổi ngay sau khi publish Remote Config.

## Animation

Ảnh Shimeji chuẩn được map theo https://github.com/gil/shimeji-ee/blob/master/conf/actions.xml (lưu bản gốc standard-actions.xml).
Nếu archive có actions.xml thì ưu tiên cấu hình đó. Các bộ ảnh không đủ frame Walk được ghi vào báo cáo và chưa đưa vào catalog để tránh ghép sai.
Renderer hiện tại chạy tick 100 ms và không đọc Duration/velocity trong XML; không thể tái hiện toàn bộ hành vi Shimeji chỉ bằng JSON.
Bản full animation được tải và lưu riêng; catalog hiện dùng gói tải chính, không tự trộn các bản có hành vi khác.
is_lock mặc định false, có thể chỉnh trước khi tạo/publish catalog theo chính sách sản phẩm.

## Chạy lại và kiểm tra

    python download_pets.py
    python download_mega.py
    python download_full.py
    python build_catalog.py --base-url https://raw.githubusercontent.com/YOUR_ACCOUNT/YOUR_REPO/BRANCH
    python validate_catalog.py

Dependencies: requests, gdown, pycryptodome, Pillow.

Nguồn sheet: https://docs.google.com/spreadsheets/d/1CrZ9A5X6xOhaPZfz6Dlo97PpwGd-sesXsdqYv-KQ6y4/edit?gid=543801201#gid=543801201


## Kết quả tải và kiểm tra

- Đủ 1081/1081 gói chính và 20/20 gói full animation.
- 49603 file ảnh/XML của gói chính.
- Catalog 1081 pet, 16206 ảnh được tham chiếu đã kiểm tra đọc được; ID không trùng.
- Flygon (632) và Ace (651) thiếu chuỗi Walk đầy đủ, đang dùng preview tĩnh. Xem reports/summary.json.
- Chưa kiểm tra tải từ GitHub/app thực tế vì chưa có repo đích; URL OWNER/REPO phải được thay bằng script build_catalog.py.
- Không sửa mã nguồn hay thêm asset vào Android project.
