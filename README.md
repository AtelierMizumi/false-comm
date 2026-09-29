# ⚡ false-comm

[![CI](https://github.com/AtelierMizumi/false-comm/actions/workflows/ci.yml/badge.svg)](https://github.com/AtelierMizumi/false-comm/actions/workflows/ci.yml)
[![Release](https://github.com/AtelierMizumi/false-comm/actions/workflows/release.yml/badge.svg)](https://github.com/AtelierMizumi/false-comm/actions/workflows/release.yml)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

> **Realistic, stealth Git commit history synthesizer for developers.**  
> *Generate mathematically organic contribution heatmaps, meaningful semantic diffs, and natural developer work rhythms across Linux distributions and major platforms.*

---

## 🌐 Languages / Ngôn ngữ
- [English Documentation](#-english-documentation) (Default / Primary)
- [Tài liệu Tiếng Việt](#-tài-liệu-tiếng-việt)

---

# 🇬🇧 English Documentation

## 🎯 Philosophy & Core Features

Most "fake commit" scripts are immediately caught by anyone who inspects `git log` or the GitHub activity graph:
1. **Artificial Fingerprints:** Exact round timestamps (`00:00:00`, `12:00`, `15:30`), identical intervals, committing on holidays or at 3:00 AM on a Sunday.
2. **Empty or Junk Diffs:** Empty commits (`--allow-empty`), trivial whitespace tweaks, or meaningless `.txt` edits that scream artificial generation upon the slightest inspection.
3. **Flat Linear Graph:** Zero branch structure, zero pull requests, zero merge commits.
4. **Dangerous & Irreversible:** No snapshot mechanism to undo changes cleanly.

### What Makes `false-comm` Different:
- **Zero-Config Interactive Mission Control:** Just type `false-comm` in your terminal to launch an intuitive TUI wizard that walks you through previewing, backfilling, auditing, and replaying.
- **Stealth & Authenticity Audit Engine (`false-comm audit`):** Scans your git history for bot fingerprints (exact round seconds, constant delta intervals, empty diffs, unnatural hours) and scores your repository authenticity from 0 to 100 with actionable stealth recommendations.
- **TrueColor GitHub Heatmap & Sparklines:** Realistic 24-bit TrueColor terminal contribution grid with dynamic month headers, weekday labels, activity streak analytics, and sparkline velocity trends.
- **Natural Date Expressions:** No need to look up calendars — specify relative human spans like `30d`, `90d`, `6m`, `1y`, `today`, `yesterday` directly in CLI commands.
- **Negative Binomial & Gamma-Poisson Sampling:** Daily commit counts follow real human productivity patterns with natural bursts and sprint streaks.
- **Intra-Day Jitter & Non-Round Minutes:** Stratified work hours (morning, afternoon, evening), lunch dip suppression (12:00–13:00), asymmetric minutes and seconds (never clustered on exact quarters).
- **Holiday & Vacation Calendars:** Automatic suppression on national holidays (US, Vietnam, Global) and synthetic 1–3 week vacation blocks per year.
- **Semantic Incremental Diffs:** Produces realistic documentation improvements, architectural notes, configuration schemas, and test fixtures tailored to the repository's primary language.
- **Replay Mode (Killer Feature):** Takes a single monolithic commit and deconstructs it into progressive, atomic commits (`models/types` ➔ `core logic` ➔ `tests` ➔ `docs`) spread across working hours over several days.
- **Branch & Merge Simulation:** Periodically spawns feature branches (`feat/rate-limiting`, `fix/memory-leak`) with realistic GitHub-style merge commits (`Merge pull request #14 from feat/...`).
- **Atomic Snapshots & Rollback:** Automatically records the exact HEAD SHA, branch, and stash before execution. Roll back anytime with `false-comm undo`.
- **First-Class Linux Support:** Built and tested across diverse Linux distributions (Ubuntu/Debian, Arch Linux, Fedora, Alpine) as well as Docker containers and POSIX environments.
- **Rewarding Completion Experience:** Closes each synthesis with an executive celebration card detailing commits created, timeline spanned, safety guarantees, and recommended next actions.

---

## 📦 Universal Installation & Distribution Packages

`false-comm` provides multiple installation methods tailored for every platform and Linux package manager:

### 1. One-Line Universal Installer (Linux / macOS / WSL)
The fastest way to install on any Unix-like system. Automatically detects your environment, chooses the optimal isolated tool runner (`uv` or `pipx`), or installs the standalone binary:
```bash
curl -fsSL https://raw.githubusercontent.com/AtelierMizumi/false-comm/main/install.sh | bash
```
*To customize destination directory (default is `~/.local/bin`):*
```bash
curl -fsSL https://raw.githubusercontent.com/AtelierMizumi/false-comm/main/install.sh | bash -s -- --dir /usr/local/bin
```

---

### 2. Arch Linux & AUR (`PKGBUILD`)
`false-comm` provides native Arch packaging in `packaging/arch/`:

**Install from AUR:**
```bash
yay -S false-comm
# Or development git version
yay -S false-comm-git
```

**Build manually with `makepkg`:**
```bash
cd packaging/arch
makepkg -si
```

---

### 3. Debian / Ubuntu (`.deb`)
Download the pre-compiled `.deb` package from the [GitHub Releases](https://github.com/AtelierMizumi/false-comm/releases) page:
```bash
# Download latest release package
sudo dpkg -i false-comm_2.0.0_amd64.deb

# Or build locally
./packaging/scripts/build_deb.sh
```

---

### 4. Fedora / RHEL / CentOS (`.rpm`)
Build and install via the native `.spec` file in `packaging/rpm/`:
```bash
rpmbuild -ba packaging/rpm/false-comm.spec
sudo dnf install ~/rpmbuild/RPMS/noarch/false-comm-2.0.0-1*.rpm
```

---

### 5. Standalone Single Binary (Zero Dependencies)
Download the standalone executable directly from [Releases](https://github.com/AtelierMizumi/false-comm/releases). No Python runtime or virtualenv required:
```bash
curl -L -o ~/.local/bin/false-comm https://github.com/AtelierMizumi/false-comm/releases/latest/download/false-comm-linux-x86_64
chmod +x ~/.local/bin/false-comm
ln -sf ~/.local/bin/false-comm ~/.local/bin/fc
```

---

### 6. Install via uv or pipx
```bash
# Recommended: Isolated tool installation
uv tool install false-comm

# Or via pipx
pipx install false-comm
```

---

## 🚀 Quick Start & CLI Reference

After installation, the primary hero command is **`false-comm`**, with **`fc`** available as an optional shorthand alias.

### 0. Interactive Mission Control Wizard (Zero Arguments)
Simply type `false-comm` in your repository to launch the guided interactive setup:
```bash
false-comm
```
*(Or explicitly launch with `false-comm wizard`)*

---

### 1. Stealth & Authenticity Audit (`audit`)
Scan your repository commit history to check if your commits look organic or if they trigger bot detection heuristics:
```bash
false-comm audit

# Inspect last 1,000 commits or filter by author
false-comm audit --max 1000 --author "you@example.com"

# Export report as JSON for CI or automation
false-comm audit --json
```

---

### 2. Diagnostic Health Check (`doctor`)
Check Git configuration, author identity, repository cleanliness, and Linux environment:
```bash
false-comm doctor
```

---

### 3. Terminal Contribution Heatmap Preview (`preview`)
Preview the synthesized contribution heatmap with TrueColor palette and activity sparklines without writing commits:
```bash
# Relative human durations
false-comm preview --from 90d --profile standard
false-comm preview --from 30d
false-comm preview --from 1y

# Or explicit date range
false-comm preview --from 2024-01-01 --to 2024-03-31 --profile standard
```

---

### 4. Synthesize Past Commit History (`backfill`)
Generate realistic commits over a date range:
```bash
# Safe preview mode (dry-run)
false-comm backfill --from 90d --dry-run

# Interactive run with progress bar & celebration card
false-comm backfill --from 90d --profile standard

# Non-interactive script run with deterministic seed
false-comm backfill --from 6m --seed 42 --yes
```

---

### 5. Replay Mode (`replay`) — *Killer Feature*
Partition a monolithic commit into a multi-day progression of atomic commits:
```bash
# Deconstruct HEAD commit across 7 business days
false-comm replay HEAD --span 7d

# Or deconstruct a specific commit SHA
false-comm replay a1b2c3d --span 5d --profile grinder
```

---

### 6. Instant Rollback (`undo`)
Restore your repository state to the safety checkpoint taken before the run:
```bash
# Undo the most recent run
false-comm undo

# List all available snapshots
false-comm undo --list

# Restore a specific snapshot
false-comm undo --snapshot snap_20240315_142010_a1b2c3
```

---

### 7. Behavioral Profiles (`profiles`)
```bash
false-comm profiles
```
- **`standard`**: Professional software engineer (9–5 core, high weekday consistency, weekend rest, lunch dip).
- **`grinder`**: Startup / hackathon engineer (high frequency, evening & weekend activity, rapid bursts).
- **`opensource`**: Maintainer / hobbyist (evenings 19:00–23:00 and weekends, quiet weekdays).
- **`student`**: Irregular sprints, deadline crunches, sporadic bursts.

---

## 🌍 Internationalization (i18n)

Switch between languages with `--lang` or the `FALSE_COMM_LANG` environment variable:
```bash
# English (Default)
false-comm --lang en doctor

# Vietnamese
false-comm --lang vi doctor

# Or via environment variable
export FALSE_COMM_LANG=vi
false-comm profiles
```

---

## ⏰ Linux Automation: Systemd User Service & Timer

Automate scheduled commit maintenance seamlessly in the background without cron clutter:
```bash
# Copy systemd units to user service directory
mkdir -p ~/.config/systemd/user/
cp packaging/systemd/false-comm.service ~/.config/systemd/user/
cp packaging/systemd/false-comm.timer ~/.config/systemd/user/

# Enable and start the timer
systemctl --user daemon-reload
systemctl --user enable --now false-comm.timer

# Check timer status
systemctl --user list-timers
```

---

## 🐚 Shell Completions

Pre-generated completions for `bash`, `zsh`, and `fish` are located in `packaging/completions/`:
```bash
# Bash
sudo cp packaging/completions/bash /usr/share/bash-completion/completions/false-comm
sudo cp packaging/completions/bash /usr/share/bash-completion/completions/fc

# Zsh
sudo cp packaging/completions/zsh /usr/share/zsh/site-functions/_false-comm
sudo cp packaging/completions/zsh /usr/share/zsh/site-functions/_fc

# Fish
sudo cp packaging/completions/fish /usr/share/fish/vendor_completions.d/false-comm.fish
```

---

# 🇻🇳 Tài liệu Tiếng Việt

## 🎯 Triết lý & Tính năng Cốt lõi

Các công cụ tạo commit ảo thông thường rất dễ bị phát hiện bởi:
1. **Dấu vân tay nhân tạo:** Commit vào các phút tròn (`:00`, `:15`, `:30`, `:45`), tần suất đều đặn như máy móc, commit vào cả ngày lễ, Tết hoặc 3h sáng Chủ Nhật.
2. **Diff rỗng hoặc vô nghĩa:** Commit rỗng (`--allow-empty`) hoặc chỉnh sửa file linh tinh không có nghĩa.
3. **Graph phẳng lì:** 100% commit thẳng vào `main`, không có branch, không có merge commit.
4. **Không an toàn:** Không có cơ chế sao lưu và hoàn tác.

`false-comm` 2.0 khắc phục hoàn toàn với:
- **Trung tâm Điều khiển Tương tác (Mission Control):** Chỉ cần gõ `false-comm` để khởi động menu wizard hướng dẫn từng bước từ xem trước, chạy thử, kiểm toán đến hoàn tác.
- **Kiểm toán Tàng hình & Độ chân thực (`false-comm audit`):** Quét toàn bộ commit hiện có trong repo để phát hiện dấu hiệu bot (giây tròn :00, khoảng cách commit đều đặn máy móc, commit rỗng), chấm điểm độ chân thực từ 0 đến 100 và đưa ra lời khuyên khắc phục cụ thể.
- **Ma trận Đóng góp TrueColor & Biểu đồ Sparkline:** Hiển thị heatmap chuẩn GitHub với dải màu 24-bit TrueColor, nhãn tháng động và dòng biểu đồ xu hướng vận tốc commit.
- **Thời gian Tự nhiên:** Hỗ trợ cú pháp thân thiện như `--from 30d`, `--from 90d`, `--from 6m`, `--from 1y` mà không cần tra cứu lịch.
- **Phân phối Negative Binomial:** Mô phỏng số commit mỗi ngày theo quy luật sinh học con người.
- **Intra-Day Jitter:** Giờ làm việc phân tầng (sáng, chiều, tối), khoảng nghỉ trưa (12h-13h), phút/giây phi đối xứng.
- **Lịch Nghỉ lễ & Nghỉ phép:** Hỗ trợ lịch nghỉ lễ Việt Nam (Tết Âm lịch, 10/3, 30/4, 1/5, 2/9) và tự động tạo 1–3 tuần nghỉ phép mỗi năm.
- **Replay Mode:** Phân rã 1 commit nguyên khối khổng lồ (viết lúc nửa đêm) thành chuỗi commit nguyên tử theo từng giai đoạn phát triển trải đều nhiều ngày.
- **Mô phỏng Nhánh & Merge:** Tự động tạo feature branch và merge commit chuẩn GitHub/GitLab.
- **Hoàn tác Nguyên tử:** Lưu snapshot an toàn trước mỗi lần chạy; khôi phục sạch sẽ chỉ với `false-comm undo`.
- **Thẻ Chúc mừng Hoàn thành:** Tổng kết chi tiết kết quả sau khi chạy cùng hướng dẫn các bước tiếp theo, mang lại cảm giác công việc được hoàn tất trọn vẹn và an tâm.

## 📦 Cách Cài Đặt Cho Từng Hệ Thống

### 1. Cài đặt 1 dòng lệnh bằng curl (Tự động nhận diện mọi OS):
```bash
curl -fsSL https://raw.githubusercontent.com/AtelierMizumi/false-comm/main/install.sh | bash
```

### 2. Dành cho Arch Linux & AUR:
```bash
yay -S false-comm
# hoặc tự build:
cd packaging/arch && makepkg -si
```

### 3. Dành cho Ubuntu / Debian (.deb):
```bash
sudo dpkg -i false-comm_2.0.0_amd64.deb
```

### 4. Binary độc lập (Không cần cài Python):
Tải trực tiếp từ [GitHub Releases](https://github.com/AtelierMizumi/false-comm/releases), phân quyền thực thi và chạy ngay:
```bash
chmod +x false-comm
./false-comm doctor
```

## 🚀 Các lệnh thường dùng

Lệnh chính của công cụ là **`false-comm`** (có thể dùng **`fc`** làm tên gọi tắt).

```bash
# Khởi động trung tâm điều khiển tương tác (wizard)
false-comm

# Kiểm toán độ chân thực của repo (phát hiện dấu vết bot)
false-comm audit

# Kiểm tra môi trường hệ thống và cấu hình git
false-comm --lang vi doctor

# Xem danh sách các hồ sơ hành vi
false-comm --lang vi profiles

# Xem trước heatmap ma trận đóng góp (90 ngày qua)
false-comm --lang vi preview --from 90d --profile standard

# Chạy tạo commit trong quá khứ với thẻ tổng kết chúc mừng
false-comm --lang vi backfill --from 90d --profile standard

# Phân rã commit nguyên khối thành nhiều commit tự nhiên
false-comm --lang vi replay HEAD --span 7d

# Hoàn tác trạng thái trước đó an toàn tuyệt đối
false-comm --lang vi undo
```

---

## ⚖️ License
Distributed under the **MIT** License. See [LICENSE](LICENSE) for details.
