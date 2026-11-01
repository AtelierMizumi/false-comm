# Kế hoạch phát triển: Replay Dry-Run + JSON Plan Export

- **Ngày**: 2026-11-01
- **Trạng thái**: Đang thực hiện
- **Phiên bản mục tiêu**: `2.1.0`
- **Người thực hiện**: AI agent + Thuận

---

## 1. Mục tiêu

Bổ sung chế độ **an toàn, không tương tác** cho lệnh `replay`:

1. `false-comm replay <ref> --dry-run`
   - Phân tích commit, phân rã thành các bước, in preview table.
   - **Không** tạo snapshot, branch, commit; HEAD/working tree không đổi.
2. `false-comm replay <ref> --json`
   - Xuất kế hoạch replay dưới dạng JSON hợp lệ ra stdout.
   - `--json` **ngầm định** dry-run (không mutate repo) để an toàn cho CI/script.
3. `--json` kết hợp `--dry-run` hoạt động giống hệt `--json`.

### Lý do chọn tính năng này

- `backfill` đã có `--dry-run`, nhưng `replay` — tính năng được quảng bá là *killer feature* — chưa có.
- Hiện tại `replay` luôn chạy preview + confirm rồi execute; không có cách nào kiểm tra kế hoạch một cách non-interactive mà không mutate repository.
- JSON output mở đường cho automation/CI kiểm tra plan trước khi áp dụng, đồng thời là nền tảng cho các tích hợp sau này.
- Phạm vi gọn, rủi ro thấp, tận dụng nguyên vẹn `ReplayAnalyzer` + `DiffRepartitioner`.

---

## 2. Phạm vi

### Trong phạm vi
- Thêm option `--dry-run` / `-d` và `--json` cho command `replay`.
- Tách hàm tạo payload JSON thuần (dễ unit test).
- i18n key cho thông báo dry-run (en + vi).
- Cập nhật README và man page.
- Test unit + integration cho toàn bộ hành vi trên.

### Ngoài phạm vi
- Thay đổi thuật toán phân rã (`DiffRepartitioner`).
- Replay nhiều commit / range.
- Thêm màn hình dry-run vào wizard.
- Sửa các bug không liên quan (ví dụ chuỗi i18n `celebrate.target_branch`).

---

## 3. Đặc tả hành vi

| Lệnh | Kết quả | Mutate repo? |
|---|---|---|
| `replay REF --dry-run` | In bảng preview + dòng thông báo dry-run | Không |
| `replay REF --dry-run --json` | In JSON plan | Không |
| `replay REF --json` | In JSON plan (tự động dry-run) | Không |
| `replay REF --yes` | Hành vi cũ: preview → snapshot → replay | Có |
| `replay REF --dry-run` với ref sai | In lỗi `Failed to inspect commit...` | Không |
| `replay REF --dry-run` ngoài git repo | In lỗi `not a valid Git repository` | Không |

### JSON schema

```json
{
  "commit": "<ref do người dùng truyền vào>",
  "original_message": "feat: ...",
  "span_days": 3,
  "total_files": 4,
  "total_steps": 4,
  "steps": [
    {
      "step_index": 1,
      "phase": "interface_schema",
      "message": "feat(models): define data models and configuration schemas",
      "files": ["models/user.py"]
    }
  ]
}
```

- Key luôn là tiếng Anh, không phụ thuộc `--lang`.
- JSON phải parse được bằng `json.loads()` từ stdout, không bị Rich cắt dòng.

---

## 4. Thiết kế kỹ thuật

### Các file thay đổi

| File | Thay đổi |
|---|---|
| `src/false_comm/cli/app.py` | Thêm option `--dry-run/-d`, `--json`; truyền xuống `handle_replay` |
| `src/false_comm/cli/replay_cmd.py` | Thêm params `dry_run`, `json_output`; `build_replay_plan_payload()`; early return trước khi tạo snapshot |
| `src/false_comm/i18n/catalog.py` | Thêm `replay.dry_run_notice` (en/vi) |
| `tests/conftest.py` | Thêm fixture `monolithic_commit` dùng chung |
| `tests/integration/test_replay_dry_run.py` | Test CLI dry-run + JSON |
| `tests/unit/test_replay_payload.py` | Test hàm build payload |
| `README.md` | Ví dụ dry-run/JSON trong mục Replay |
| `packaging/man/false-comm.1` | Cập nhật synopsis + mô tả option |

### Luồng xử lý

```
handle_replay()
  ├─ validate git repo
  ├─ parse span
  ├─ load profile
  ├─ analyze commit + partition steps
  ├─ if json_output: print JSON payload → return
  ├─ print preview table
  ├─ if dry_run: print notice → return
  ├─ confirm (nếu không --yes)
  ├─ snapshot + execute_replay
```

Điểm mấu chốt: mọi nhánh dry-run/JSON phải return **trước** `SnapshotManager(adapter)` và `CommitReplayer`.

---

## 5. Kế hoạch TDD

- [x] **Bước 1**: Thêm fixture `monolithic_commit` vào `tests/conftest.py`.
- [x] **Bước 2**: Viết test mới (chưa sửa production code):
  - [x] `test_replay_dry_run_previews_without_mutating`
  - [x] `test_replay_dry_run_json_emits_parseable_plan`
  - [x] `test_replay_json_flag_alone_implies_dry_run`
  - [x] `test_replay_dry_run_rejects_invalid_commit_without_mutating`
  - [x] `test_replay_dry_run_outside_git_repo`
  - [x] `test_build_replay_plan_payload_shape` (unit)
- [x] **Bước 3**: Chạy test, xác nhận **RED** vì option chưa tồn tại.
- [x] **Bước 4**: Implement tối thiểu để GREEN.
- [x] **Bước 5**: Refactor + cập nhật README/man page.
- [x] **Bước 6**: Chạy full gate: `pytest`, `ruff check`, `ruff format --check`, `mypy src`.
- [x] **Bước 7**: Báo cáo kết quả kèm output thật.

---

## 6. Test matrix

| Case | Kỳ vọng |
|---|---|
| Dry-run happy path | Exit 0, preview table, notice, HEAD/branches/snapshots không đổi |
| JSON happy path | Exit 0, JSON parse được, đúng steps/phases/files, repo không đổi |
| `--json` không kèm `--dry-run` | Vẫn không mutate |
| Ref không tồn tại | Exit 0, thông báo lỗi, repo không đổi |
| Ngoài git repo | Exit 0, thông báo lỗi |
| Dry-run + `--yes` | Không mutate (dry-run thắng) |
| Payload builder | Đúng schema, `phase` serialize thành string |

---

## 7. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| JSON bị lẫn output Rich/ANSI | In JSON bằng `print()` trước khi render bất kỳ thứ gì; test parse trực tiếp |
| Vô tình tạo snapshot trước khi return | Đặt toàn bộ nhánh dry-run/JSON trước `SnapshotManager`; test assert snapshot dir rỗng |
| Thay đổi phá vỡ wizard | Giữ default `dry_run=False`, `json_output=False`; wizard không truyền tham số mới |
| `--json` gây hiểu nhầm là có execute | Tài liệu + help text ghi rõ "implies --dry-run" |

---

## 8. Definition of Done

- [x] Tất cả test mới xanh, không có test cũ bị sửa yếu đi.
- [x] Full suite pass; coverage không giảm.
- [x] `ruff`, `mypy` sạch.
- [x] README + man page có ví dụ.
- [x] Không mutate repo khi dry-run/JSON (có test chứng minh).
- [x] Báo cáo RED → GREEN kèm output thật.

---

## 9. Nhật ký thực hiện (2026-11-01)

### RED

```
$ uv run pytest tests/integration/test_replay_dry_run.py tests/unit/test_replay_payload.py -q
6 failed ... No such option: --dry-run
1 error ... ImportError: cannot import name 'build_replay_plan_payload'
```

### GREEN

```
$ uv run pytest -q
96 passed in 9.15s

$ uv run ruff check .                 → All checks passed!
$ uv run ruff format --check .        → 65 files already formatted
$ uv run mypy src                     → Success: no issues found in 40 source files
```

### Coverage

| File | Trước | Sau |
|---|---|---|
| `cli/replay_cmd.py` | 87% | **97%** |
| TOTAL | 87% | 87% (2193 stmts) |

### Kiểm chứng CLI thật

```
$ false-comm replay <sha> --span 3d --dry-run
... preview table ...
Dry-run mode: no commits, branches, or snapshots were created.

$ false-comm replay <sha> --span 3d --json
{ "commit": "...", "span_days": 3, "total_steps": 4, "steps": [...] }

$ git rev-parse HEAD      → không đổi
$ git branch              → chỉ còn main
$ git status --porcelain  → rỗng
$ snapshot dir            → 0 file
```
