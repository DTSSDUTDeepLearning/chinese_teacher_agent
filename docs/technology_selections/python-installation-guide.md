# Python 3.11.9 安装指南

本指南提供 Windows 操作系统下 Python 3.11.9 的详细安装步骤，可供自动化助手按步骤执行安装。

---

## 一、下载安装包

1. 打开浏览器，访问官方下载地址：
   - 地址：https://www.python.org/downloads/release/python-3119/
   - 或直接访问：https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

2. 在页面中找到 "Windows installer (64-bit)" 链接，文件名为 `python-3.11.9-amd64.exe`。

3. 点击下载，等待下载完成。文件大小约 25-30 MB。

---

## 二、运行安装程序

1. 打开文件下载目录（默认为 `Downloads` 文件夹）。

2. 找到下载的文件 `python-3.11.9-amd64.exe`。

3. **关键步骤**：双击运行安装程序。

4. 安装向导启动后，显示的第一个页面底部有两个选项：
   - `☐ Add python.exe to PATH`（默认未勾选）
   - `☐ Disable path length limit`（默认未勾选）

5. **必须操作**：勾选 `Add python.exe to PATH`。此步骤至关重要，否则后续无法在命令行中直接使用 `python` 命令。

6. 点击页面下方的 `Customize installation`（自定义安装）按钮。

---

## 三、可选功能页面

1. 进入 "Optional Features" 页面，保持默认勾选状态即可：
   - `☑ Documentation`
   - `☑ pip`
   - `☑ tcl/tk and IDLE`
   - `☑ Python test suite`
   - `☑ py launcher`
   - `☑ for all users`

2. 点击 `Next` 按钮进入下一步。

---

## 四、高级选项页面

1. 进入 "Advanced Options" 页面，建议勾选以下选项：
   - `☑ Install for all users`（为所有用户安装）
   - `☑ Associate files with Python`（将文件与 Python 关联）
   - `☑ Create shortcuts for installed applications`（创建快捷方式）
   - `☑ Add Python to environment variables`（添加 Python 到环境变量）
   - `☐ Precompile standard library`（可选，预编译标准库，会延长安装时间）
   - `☐ Download debugging symbols`（不需要）
   - `☐ Download debug binaries`（不需要）

2. 自定义安装路径（可选）：
   - 默认路径为 `C:\Program Files\Python311`
   - 如需修改，点击 `Browse` 按钮选择新路径
   - 建议保持默认路径

3. 点击 `Install` 按钮开始安装。

4. 等待安装完成，进度条走完后显示 "Setup was successful"。

5. 点击 `Close` 按钮关闭安装向导。

---

## 五、禁用路径长度限制（可选但推荐）

1. 如果安装结束时弹出了 "Disable path length limit" 的提示，点击 `Yes` 确认。

2. 此操作移除 Windows 260 字符路径长度限制，避免后续使用中的潜在问题。

---

## 六、验证安装

1. 按 `Win + R` 键打开运行对话框。

2. 输入 `cmd` 并按回车，打开命令提示符窗口。

3. 在命令行中输入以下命令并按回车：
   ```bash
   python --version
   ```

4. 预期输出：
   ```
   Python 3.11.9
   ```

5. 继续输入以下命令验证 pip 是否安装成功：
   ```bash
   pip --version
   ```

6. 预期输出（版本号可能略有不同）：
   ```
   pip 24.0 from ...\site-packages\pip (python 3.11)
   ```

7. 如果以上命令均返回正确结果，说明 Python 3.11.9 安装成功。

---

## 七、常见问题

| 问题 | 解决方案 |
|------|----------|
| 命令行输入 `python` 提示找不到命令 | 安装时未勾选 "Add python.exe to PATH"。可重新运行安装程序选择 "Modify" 并勾选该选项，或手动添加环境变量。 |
| 系统中已安装其他 Python 版本 | 可在命令行中使用 `py -3.11` 明确指定 3.11 版本，或调整 PATH 环境变量的优先级顺序。 |
| 安装过程中提示权限不足 | 右键点击安装程序，选择 "以管理员身份运行"。 |
